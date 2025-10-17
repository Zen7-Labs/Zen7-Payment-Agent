from log import logger
import asyncio

from dotenv import load_dotenv
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from host_agent.agent import host_agent
# from remote_agents.agent import remote_host_agent

from utils import add_user_query_to_history, call_agent_async


load_dotenv()

session_service = InMemorySessionService()

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
USER_ID = "zen7_payment_agent"

async def main_async():
    
    new_session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        state=initial_state
    )

    SESSION_ID = new_session.id
    logger.info(f"Created new session: {SESSION_ID}")
   
    runner = Runner(
        agent=host_agent,
        app_name=APP_NAME,
        session_service=session_service
    )

    logger.info(f"\nWelcome to Zen7 Payment Agent")
    logger.info("Type 'exit' or 'quit' to end the conversation.\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            logger.info("Ending conversation. Goodbye!")
            break
        await add_user_query_to_history(session_service, APP_NAME, USER_ID, SESSION_ID, user_input)
        await call_agent_async(runner, USER_ID, SESSION_ID, user_input)

    final_session = await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    logger.info(f"\nFinal session state:")
    for key, value in final_session.state.items():
        logger.info(f"{key}: {value}")

if __name__ == "__main__":
    asyncio.run(main_async())
