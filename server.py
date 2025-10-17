from fastapi import FastAPI, Request, Depends
from contextlib import asynccontextmanager

from log import logger

from dotenv import load_dotenv
from google.adk.sessions import InMemorySessionService
from google.adk.sessions.base_session_service import ListSessionsResponse
from google.adk.runners import Runner
from host_agent.agent import host_agent
from utils import add_user_query_to_history, call_agent_async

from typing import Annotated, Tuple

import uvicorn
import os

from services.order.order_service import get_order_item

load_dotenv()


initial_state = {
    "order_number": "",
    "spend_amount": 0,
    "budget": 0,
    "expiration_date": "",
    "currency": "",
    "sign_info": {},
    "owner_wallet_address": ""
}

APP_NAME = "Zen7 Payment Agent"

class AppWideService:
    def __init__(self, APP_NAME, session_service, runner):
        self.app_name = APP_NAME
        self.session_service = session_service
        self.runner = runner

    def get_shared_resources(self) -> Tuple[InMemorySessionService, Runner]:
        return self.session_service, self.runner

@asynccontextmanager
async def lifespan(app: FastAPI):
    session_service = InMemorySessionService()
    runner = Runner(
        agent=host_agent,
        app_name=APP_NAME,
        session_service=session_service
    )
    shared_service = AppWideService(APP_NAME, session_service, runner)
    app.state.shared_service = shared_service
    yield {"shared_service": shared_service}
    
app = FastAPI(lifespan=lifespan)

def get_shared_service() -> AppWideService:
    return app.state.shared_service

@app.post("/chat_a2a")
async def chat(request: Request, service: Annotated[AppWideService, Depends(get_shared_service)]):
    data = await request.json()
    message = data["message"]
    user_id_from_request: str = data.get("user_id", "user_01") 
    if not user_id_from_request:
        return {"error": "user_id is required in the request body"}, 400
    logger.info(f"Received parameter for User ID '{user_id_from_request}'")

    sign_info_from_request: dict[str, any] = data.get("sign_info", {})
    logger.info(f"Received parameter for Sign Info '{sign_info_from_request}'")

    owner_wallet_address_from_request: str = data.get("owner_wallet_address", "")
    logger.info(f"Received parameter for Owner wallet address '{owner_wallet_address_from_request}'")

    payment_info_from_request: dict[str, any] = data.get("payment_info", {})
    logger.info(f"Received parameter for Payment info '{payment_info_from_request}'")
    
    timezone_from_request: str = data.get("timezone", "Asia/Shanghai")
    logger.info(f"Received parameter for Timezone: '{timezone_from_request}'")

    initial_state["sign_info"] = sign_info_from_request
    initial_state["owner_wallet_address"] = owner_wallet_address_from_request
    initial_state["payment_info"] = payment_info_from_request
    initial_state["timezone"] = timezone_from_request
  
    session_service, runner = service.get_shared_resources()
    session_id = None
    result = await session_service.list_sessions(app_name=APP_NAME, user_id=user_id_from_request)
    empty_response = ListSessionsResponse()
    if result == empty_response:
        new_session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id_from_request,
            state=initial_state
        )
        session_id = new_session.id
        logger.info(f"Created NEW session: {session_id} for user: {user_id_from_request}")
    else:
        logger.info(f"list_sessions: {result}")
        for s in result.sessions:
            if s.user_id == user_id_from_request:
                session_id = s.id
                break
        current_session = await session_service.get_session(
            app_name=APP_NAME, 
            user_id=user_id_from_request,
            session_id=session_id
        )
        session_id = current_session.id

        updated_state = current_session.state.copy()
        updated_state["sign_info"] = sign_info_from_request
        updated_state["owner_wallet_address"] = owner_wallet_address_from_request
        updated_state["payment_info"] = payment_info_from_request
        updated_state["timezone"] = timezone_from_request

        await session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id_from_request,
            session_id=session_id,
            state=updated_state
        )
        logger.info(f"Loaded existing session: {session_id} for user: {user_id_from_request}")
        
    await add_user_query_to_history(session_service, APP_NAME, user_id_from_request, session_id, message)
    resp_body = await call_agent_async(runner, user_id_from_request, session_id, message)
    return {"response": resp_body}

@app.put("/reset")
async def reset(request: Request, service: Annotated[AppWideService, Depends(get_shared_service)]):
    user_id_from_request: str = request.query_params.get("user_id", "user_01") 
    if not user_id_from_request:
        return {"error": "user_id is required in the request body"}, 400
    logger.info(f"Received user ID '{user_id_from_request}")
    session_service, _ = service.get_shared_resources()
    result = await session_service.list_sessions(app_name=APP_NAME, user_id=user_id_from_request)
    empty_response = ListSessionsResponse()
    if result != empty_response:
        logger.info(f"list_sessions: {result}")
        for s in result.sessions:
            if s.user_id == user_id_from_request:
                session_id = s.id
                await session_service.delete_session(app_name=APP_NAME, user_id=user_id_from_request, session_id=session_id)
                return {"message": f"Session for user_id: {user_id_from_request} has been reset."}
    return {"error": f"No session found for user_id: {user_id_from_request}"}

@app.get("/status")
async def get_order_status(request: Request):
    order_number_from_request = request.query_params.get("order_number")
    if not order_number_from_request:
        return {"error": "order_number is required"}, 400
    user_id_from_request = request.query_params.get("user_id")
    if not user_id_from_request:
        return {"error": "user_id is required"}, 400
    logger.info(f"Received order number: '{order_number_from_request}', user id: {user_id_from_request}")
    try:
        res = get_order_item(order_number_from_request)
        if res:
            logger.info(f"Get order item: {res} by order_number: {order_number_from_request}")
            return {
                "status": res["status"],
                "message": res["status_message"]
            }
    except:
        return {
            "status": "UNKNOWN",
            "message": f"None of status found by order number: {order_number_from_request} and user_id: {user_id_from_request}"
        }
    
if __name__ == "__main__":
    host = os.getenv("ZEN7_PAYMENT_SERVER_HOST")
    port = os.getenv("ZEN7_PAYMENT_SERVER_PORT")
    uvicorn.run("server:app", host=host, port=int(port), use_colors=False)