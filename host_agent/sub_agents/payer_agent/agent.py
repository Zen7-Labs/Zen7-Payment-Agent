from log import logger

from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext

from datetime import datetime
from services.execute_sign import sign
from utils import is_valid_date_format, convert_to_local_timezone

from dotenv import load_dotenv
import os

load_dotenv()

from services.order.order_service import add_or_update_order_item

def create_payment(order_number: str, spend_amount: float, budget: float, expiration_date: str, currency: str, tool_context: ToolContext) -> dict[str, any]:
    """
    Create payment for payer.
    """
    payment_info = tool_context.state.get("payment_info", {})

    if order_number:
        if payment_info and "order_number" in payment_info:
            logger.info(f"Got order number: {order_number} from payment_info")
            order_number = payment_info["order_number"]
        logger.info(f"Order number is: {order_number}")
        tool_context.state["user:order_number"] = order_number
    else:
        logger.error("Payment order number is unset")
        return {
            "status": "failed",
            "message": "Payment order number is unset"
        }
    if spend_amount:
        if payment_info and "spend_amount" in payment_info:
            logger.info(f"Got spend amount: {spend_amount} from payment_info")
            spend_amount = payment_info["spend_amount"]
        logger.info(f"Payer spend amount is: {spend_amount}")
        tool_context.state["user:spend_amount"] = spend_amount
    else:
        logger.error("Payer spend amount is unset")
        return {
            "status": "failed",
            "message": "Payment spend amount is unset"
        }

    if budget:
        if payment_info and "budget" in payment_info:
            logger.info(f"Got budget: {budget} from payment_info")
            budget = payment_info["budget"]
        logger.info(f"Payment budget is: {budget}")
        tool_context.state["user:budget"] = budget
    else:
        logger.error("Payment budget is unset")
        return {
            "status": "failed",
            "message": "Payment budget is unset"
        }
    
    if spend_amount > budget:
        logger.info("Payment spend amount exceeded budget.")
        return {
            "status": "failed",
            "message": "Payment spend amount exceeded budget"
        }

    if not expiration_date:
        logger.error(f"Payment expiration date is unset")
        return {
            "status": "failed",
            "message": "Payment expiration date is unset"
        }
    
    if payment_info and "expiration_date" in payment_info:
        logger.info(f"Got expiration date: {expiration_date} from payment_info")
        expiration_date = payment_info["expiration_date"]

    if is_valid_date_format(expiration_date):
        logger.info(f"Payment expiration date is: {expiration_date}")
        tool_context.state["user:expiration_date"] = expiration_date
    else:
        return {
            "status": "failed",
            "message": f"Payment expiration date {expiration_date} format is invalid."
        }
    
    if currency:
        if payment_info and "currency" in payment_info:
            logger.info(f"Got currency: {currency} from payment_info")
            currency = payment_info["currency"]
        logger.info(f"Payment currency is: {currency}")
        tool_context.state["user:currency"] = currency
    else:
        logger.error("Payment currency is unset")
        return {
            "status": "failed",
            "message": "Payment currency is unset"
        }
    
    deadline_time = datetime.strptime(expiration_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
    deadline = 0
    timezone = tool_context.state.get("timezone")
    if timezone:
        logger.info(f"Got timezone: {timezone} from context.")
        converted_time = convert_to_local_timezone(deadline_time, timezone)
        deadline = int(converted_time.timestamp())
    else:
        deadline = int(deadline_time.timestamp())

    owner_wallet_address = tool_context.state.get("owner_wallet_address")
    if owner_wallet_address:
        logger.info(f"Received owner wallet address: {owner_wallet_address} from context.")
    else:
        owner_wallet_address = os.getenv("OWNER_WALLET_ADDRESS")
        logger.info("None of owner wallet address received from context instead from env")

    add_or_update_order_item(order_number=order_number, user_id=owner_wallet_address, spend_amount=spend_amount, budget=budget, currency=currency, status="PENDING", status_message="", deadline=deadline)

    sign_info = tool_context.state.get("sign_info", {})
    logger.info(f"Sign_info from context: {sign_info}")
    signature, r, s, v = None, None, None, None
    if sign_info:
        signature = sign_info["signature"]
        r = sign_info["r"]
        s = sign_info["s"]
        v = sign_info["v"]
    else:
        signature, r, s, v = sign(budget, deadline)
        
    logger.info(f"Sign info - signature: {signature}, r: {r}, s: {s}, v: {v}")

    tool_context.state["user:deadline"] = deadline
    tool_context.state["user:signature"] = signature
    tool_context.state["user:value"] = spend_amount
    tool_context.state["user:r"] = r
    tool_context.state["user:s"] = s
    tool_context.state["user:v"] = v
    logger.info(f"Created payer payment signature: {signature} and set to context.")
    logger.info(f"=> deadline: {deadline} set to context")
    logger.info(f"=> value: {spend_amount} set to context")
    logger.info(f"=> r: {r} and set to context.")
    logger.info(f"=> s: {s} and set to context.")
    logger.info(f"=> v: {v} and set to context.")

    return {
        "status": "success",
        "message": f"Created payer payment signature: {signature} and set to context."
    }

payer_agent = LlmAgent(
    name="payer_agent",
    model="gemini-2.0-flash-lite",
    description="Payer agent for the zen7 payment to handle payment issues.",
    instruction="""
    You are the payer agent for the zen7 payment to handle payment issues.
    
    Your role is to help users create payment based on order number, spend amount, budget, expiration date and currency for USDC or DAI.
    
    Your responsibility is to
        - Create the payment by asking for order number, spend amount, budget, expiration date and currency for USDC or DAI for the payment authorization.
    
    Please make sure the payer agent to the settlement agent is a continuation step:
        - DO NOT give any confirmation, CONTINUE to invoke settlement agent and proceed settlement for this payment.
        - DO NOT wait for confirmation when the message says "will guide," "will help," "will initialize," "will start," or "will invoke." Instead, make sure to continue calling the settlement agent until the payment is processed.
        
    **Payer information:**
    order number: {order_number}
    spend amount: {spend_amount}
    budget: {budget}
    expiration date: {expiration_date}
    currency: {currency}
      
    **Interaction History:**
    <interaction_history>
    {interaction_history}
    </interaction_history>

    """,
    tools=[create_payment]
)