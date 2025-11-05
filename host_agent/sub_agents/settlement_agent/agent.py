from log import logger
from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext

from dotenv import load_dotenv
import os
import requests
import re

from services.order.order_service import add_or_update_order_item
from services.blockchain_errors import BlockchainErrorClassifier

from services.intent import collect_intent
from services.audit_event import collect_audit_event
from dao.model import AuditEventType

load_dotenv()

from task_manager.task_scoped_manager import TaskScopedServiceManager

notification_url = os.getenv("NOTIFICATION_URL")

def receive_payer_payment(tool_context: ToolContext) -> dict[str, any]:
    """
    Receive payment request from payer agent
    """
    spend_amount = tool_context.state.get("user:spend_amount")
    if spend_amount:
        logger.info(f"Received spend amount: {spend_amount} from payer agent.")
    else:
        logger.error("None of spend amount received.")
        return {
            "status": "failed",
            "message": "None of payer spend amount received."
        }

    budget = tool_context.state.get("user:budget")
    if budget:
        logger.info(f"Received budget: {budget} from payer agent.")
    else:
        logger.error("None of payer budget received.")
        return {
            "status": "failed",
            "message": "None of payer budget received."
        }
    
    expiration_date = tool_context.state.get("user:expiration_date")
    if expiration_date:
        logger.info(f"Received payer expiration date: {expiration_date} from payer agent.")
    else:
        logger.error("None of payer expiration date received.")
        return {
            "status": "failed",
            "message": "None of payer expiration date received."
        }

    signature = tool_context.state.get("user:signature")
    if signature:
        logger.info(f"Received signature: {signature} from payer agent.")
    else:
        logger.error("None of payer signature received.")
        return {
            "status": "failed",
            "message": "None of payer signature received."
        }
    
    current_interaction_history = tool_context.state.get("user:interaction_history")

    new_interaction_history = current_interaction_history.copy()
    tool_context.state["user:interaction_history"] = new_interaction_history

    receipt_from_payer = f"Received payment to settlement - spend amount: {spend_amount}, budget: {budget}, expiration date: {expiration_date}."
    return {
        "status": "success",
        "message": receipt_from_payer
    }

async def settle_payment(tool_context: ToolContext) -> dict[str, any]:
    """
    Settle the zen7 payment for the payer.
    """
    session_id = tool_context.state.get("session_id", "")
    logger.info(f"Got session ID: {session_id} from context")

    logger.info(f"Received the permission to permit from payer.")
    order_number = tool_context.state["user:order_number"]
    spend_amount = tool_context.state["user:spend_amount"]

    budget = tool_context.state["user:budget"]
    expiration_date = tool_context.state.get("user:expiration_date")
    currency = tool_context.state.get("user:currency")
    chain = tool_context.state.get("user:chain")
    deadline = tool_context.state.get("user:deadline")
    
    owner_wallet_address = tool_context.state.get("owner_wallet_address")
    if owner_wallet_address:
        logger.info(f"Received owner wallet address: {owner_wallet_address} from context.")
    else:
        owner_wallet_address = os.getenv("OWNER_WALLET_ADDRESS")
        logger.error("None of owner wallet address received from context instead from env")

    spender_wallet_address = os.getenv("SPENDER_WALLET_ADDRESS")
    logger.info(f"Permit and transfer with owner wallet address: {owner_wallet_address} spend amount: {spend_amount}, deadline: {deadline}")
    try:
        permit_transfer_result = await TaskScopedServiceManager.execute_permit_and_transfer(session_id=session_id, wallet_address=owner_wallet_address)
        if permit_transfer_result:
            tx_hash = permit_transfer_result["txHash"]
            is_success = permit_transfer_result["success"]
            event_type = None
            if is_success:
                event_type = AuditEventType.transfer_completed
            else:
                event_type = AuditEventType.transaction_failed
            collect_audit_event(session_id=session_id, chain=chain, event_type=event_type,
                            owner_address=owner_wallet_address, spender_address=spender_wallet_address,
                            amount=spend_amount, tx_hash=tx_hash)        
    except Exception as e:
        error_str = str(e)
        logger.error(f"Failed to settlement for permit_and_transfer: {error_str}")
        
        # Extract error code if present (format: [110020] message)
        error_code = None
        error_message = error_str
        match = re.match(r'\[(\d+)\]\s*(.*)', error_str)
        if match:
            error_code = match.group(1)
            error_message = match.group(2)
        else:
            # Try to classify error
            parsed = BlockchainErrorClassifier.parse_error(error_str)
            error_code = parsed["error_code"]
            error_message = parsed["user_message"]
        collect_audit_event(session_id=session_id, chain=chain, event_type=AuditEventType.transaction_failed,
                            owner_address=owner_wallet_address, spender_address=spender_wallet_address,
                            amount=spend_amount)
        # Update order status
        add_or_update_order_item(
            order_number=order_number, 
            user_id=owner_wallet_address, 
            spend_amount=spend_amount, 
            budget=budget, 
            currency=currency,
            chain=chain,
            status="FAILED", 
            status_message=error_message, 
            deadline=deadline
        )
        
        # Send notification with error code
        notification_payload = {
            "status": False,
            "order_number": order_number,
            "error_code": error_code,
            "message": error_message
        }
        res = requests.post(notification_url, json=notification_payload)
        if res.ok:
            logger.info(f"Notify settlement message by url: {notification_url} with status code: {res.status_code}")
        
        return {
            "status": "failed",
            "error_code": error_code,
            "message": f"Failed to settlement for permit_and_transfer: {error_message}"
        }
    finally:
        await TaskScopedServiceManager.release_instance(session_id=session_id, wallet_address=owner_wallet_address)

    logger.info("Settlement about the payer info:\n")
    logger.info(f"\tOrder number: {order_number}")
    logger.info(f"\tSpend amount: {spend_amount}")
    logger.info(f"\tBudget: {budget}")
    logger.info(f"\tExpiration date: {expiration_date}")
    logger.info(f"\tCurrency: {currency}")
    logger.info(f"\tChain: {chain}")
    settlement_message = f"Settlement info - order number: {order_number}, spend amount: {spend_amount}, budget: {budget}, expiration date: {expiration_date}, currency: {currency}, chain: {chain}"
    
    add_or_update_order_item(order_number=order_number, user_id=owner_wallet_address, spend_amount=spend_amount, budget=budget, currency=currency, chain=chain, status="SUCCESS", deadline=deadline)

    res = requests.post(notification_url, json={"status": True, "order_number": order_number})
    if res.ok:
        logger.info(f"Notify settlement message by url: {notification_url} with status code: {res.status_code}")
    return {
        "status": "success",
        "message": settlement_message
    }

def notify_payee(tool_context: ToolContext) -> dict[str, any]:
    '''
    Notify payee agent for reply that the settlement has finished on chain.
    '''
    order_number = tool_context.state.get("user:order_number")
    notification = f"Settlement with order number: {order_number} has been settled on chain"
    tool_context.state["user:payee_notification"] = notification
    logger.info(notification)

    return {
        "status": "success",
        "message": notification
    }

settlement_agent = LlmAgent(
    name="settlement_agent",
    model="gemini-2.0-flash-lite",
    description="Settlement agent for the zen7 payment settlement operations",
    instruction="""
    You are a settlement agent for the zen7 payment settlement operations.
    Your role is to help users finish settlement
        
    Your responsibilities are:
    - Immediately settle the payment created by payer agent.
    - IF ANYTHING NEED TO CONFIRM, DO NOT ASK TO CONFIRM, INSTEAD, IMMEDIATELY PROCEED THE SETTLEMENT
    - SHOULD notify payee agent with settlement notification ONLY IF the settlement has proceeded successfully.
    - If settlement was failed, reply the status and error message.
        
    **Interaction History:**
    <interaction_history>
    {interaction_history}
    </interaction_history>
    """,
    tools=[receive_payer_payment, settle_payment, notify_payee],
)