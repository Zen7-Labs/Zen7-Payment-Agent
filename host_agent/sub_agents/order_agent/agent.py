from log import logger
from google.adk.agents import Agent
from google.adk.tools import ToolContext

import json
from services.order.order_service import get_order_item, get_order_list_by_user


def get_order(order_number: str, tool_context: ToolContext) -> dict[str, any]:
    if order_number:
        try:
            order_item = get_order_item(order_number)
            return {
                "status": "success",
                "message": json.dumps(order_item)
            }
        except Exception as e:
            return {
                "status": "failed",
                "message": str(e)
                }
    return {
        "status": "failed",
        "message": "None of order_number found."
    }
        
def get_payer_order_list(owner_wallet_address: str, tool_context: ToolContext) -> dict[str, any]:
    if owner_wallet_address:
        logger.info(f"Owner wallet address is: {owner_wallet_address}")
        try:
            order_list = get_order_list_by_user(owner_wallet_address)
            return {
                "status": "success",
                "message": json.dumps(order_list)
            }
        except Exception as e:
            return {
                "status": "failed",
                "message": str(e)
            }
    return {
        "status": "failed",
        "message": "None of owner_wallet_address found."
    }

order_agent = Agent(
    name="QueryOrderAgent",
    model="gemini-2.0-flash-lite",
    instruction="""
        Your goal is help user query order by order number or get payer order list by owner wallet address.

        Your responsibilites are:
        - Use tool 'get_order' to get order RETURN THE DETAILS of the result by the provided order number.
        - Use tool 'get_payer_order_list' to get order list RETURN THE DETAILS of the result by the provided owner wallet address.
    """,
    tools=[get_order, get_payer_order_list]
)
