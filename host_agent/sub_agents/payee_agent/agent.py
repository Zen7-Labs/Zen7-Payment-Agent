from log import logger
from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext
import json

from services.order.order_service import get_order_item, get_order_list_by_user

def notify_payment_creator(tool_context: ToolContext) -> dict[str, any]:
    '''
    Receive settlement notification for payee from settlement agent
    '''
    notification = tool_context.state.get("user:payee_notification")
    if notification:
        logger.info(f"Received payee payment notification: {notification}")
        return {
            "status": "success",
            "message": f"Received payee payment notification: {notification}"
        }
    
    logger.error("No payee payment notification received from settlement agent")
    return {
        "status": "failed",
        "message": "No payee payment notification received from settlement agent"    
    }

def get_order(order_number: str, tool_context: ToolContext) -> dict[str, any]:
    if order_number:
        payment_info = tool_context.state.get("payment_info", {})
        if payment_info and "order_number" in payment_info:
            order_number = payment_info["order_number"]
            logger.info(f"Got order number: {order_number} from payment_info")
        logger.info(f"Order number is: {order_number}")
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
        owner_wallet_address_ctx = tool_context.state.get("owner_wallet_address")
        if owner_wallet_address_ctx:
            owner_wallet_address = owner_wallet_address_ctx
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


payee_agent = LlmAgent(
    name="payee_agent",
    model="gemini-2.0-flash-lite",
    description="Payee agent for the zen7 payment to handle payee operations.",
    instruction="""
    You are the payee agent for the zen7 payment to create order and get order or get payer order list.
    
    Your role is as payee who create order, return the order number then allow user to get the order or get the order list 
    when received the notification that the settlement has FINISHED.

    Your responsibilites are:
        - Use tool 'get_order' to get order RETURN THE DETAILS of the result by the provided order number.
        - Use tool 'get_payer_order_list' to get order list RETURN THE DETAILS of the result by the provided owner wallet address.
   
    **Interaction History:**
    <interaction_history>
    {interaction_history}
    </interaction_history>
  
    """,
    tools=[notify_payment_creator, get_order, get_payer_order_list]
)