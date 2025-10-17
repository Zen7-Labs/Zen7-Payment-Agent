import logging
from google.adk.agents.llm_agent import Agent
from google.adk.tools import ToolContext

import requests
from dotenv import load_dotenv
import os

load_dotenv()

zen7_payment_server_host = os.getenv("ZEN7_PAYMENT_SERVER_HOST")
zen7_payment_server_port = os.getenv("ZEN7_PAYMENT_SERVER_PORT")
zen7_payment_server_base_url = f"http://{zen7_payment_server_host}:{zen7_payment_server_port}"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def proceed_payment_and_settlement_and_order_details(content: str, tool_context: ToolContext) -> dict[str, any] | str | None:
    if content in ["quit", "exit"]:
        return {
            "status": "success",
            "message": "Quit per command."
        }
    else:
        user_id = tool_context.state.get("user_id")
        logger.info(f"============= Got user_id from context: {user_id} =============")
        sign_info = tool_context.state.get("sign_info", {})
        logger.info(f"============= Got sign_info from context: {sign_info} =============")
        owner_wallet_address = tool_context.state.get("owner_wallet_address")
        logger.info(f"============= Got owner_wallet_address from context: {owner_wallet_address} =============")
        payment_info = tool_context.state.get("payment_info", {})
        logger.info(f"============= Got payment_info from context: {payment_info} =============")
        timezone = tool_context.state.get("timezone")
        logger.info(f"============= Got timezone from context: {timezone} =============")
        res = requests.post(f"{zen7_payment_server_base_url}/chat_a2a", json={"message": content, "user_id": user_id, "sign_info": sign_info, "owner_wallet_address": owner_wallet_address, "payment_info": payment_info, "timezone": timezone})
        if res.ok:
            data = res.json()
            message = data["response"]
            response_content = f"{message["event"]["author"].capitalize()}: {message["final_response"]}"
            logger.info(response_content)
            return {"final_response": message["final_response"] }
        

process_with_content_agent = Agent(
    name="process_with_content",
    model="gemini-2.0-flash-lite",
    description="Process by invoking tool with provided detail info",
    instruction="""
    Your goal is to ALWAYS USE tool 'proceed_payment_and_settlement_and_order_details' to CONVEY ANY input messages.

    ***Core capabilities***
    1. Do not modify content submitted to the tool "proceed_payment_and_settlement_and_order_details"
    2. The result of the tool "proceed_payment_and_settlement_and_order_details" MUST BE RETURNED AS IS
    3. The returned content SHOULD contain the order number if the response has provided.
    """,
    tools=[proceed_payment_and_settlement_and_order_details]
)