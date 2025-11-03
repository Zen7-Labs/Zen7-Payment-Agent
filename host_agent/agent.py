from google.adk.agents import SequentialAgent, Agent
from google.adk.tools import FunctionTool, ToolContext

from .sub_agents.payer_agent import payer_agent
from .sub_agents.settlement_agent import settlement_agent
from .sub_agents.payee_agent import payee_agent
from .sub_agents.order_agent import order_agent
from .sub_agents.allowance_agent import allowance_agent
# You are the primary host agent for zen7 payment service.

# Your role is to help attendees with their questions and direct them to the appropriate specialized agent.

# You have access to the following specialized agents:
# 1. Payer Agent:
#     - Direct payer-related queries here
#     - For questions about payer to create a payment
#     - The capabilities are:
#         - Create a payment by setting order number, spend amount, budget and expiration date and currency (USDC or DAI)
#         - Always think about the payment is a new payment, DO NOT ASK TO CONFIRM ANYTHING UNTIL the settlement is COMPLETED.

#     Make sure the payer agent to the settlement agent is a continuation step:
#         - DO NOT give any confirmation, CONTINUE to invoke settlement agent and proceed settlement for this payment.
#         - DO NOT wait for confirmation when the message says "will guide," "will help," "will initialize," "will start," or "will invoke." Instead, make sure to continue calling the settlement agent until the payment is processed.
    

# 2. Settlement Agent:
#     - For questions about the created payment to settlement.
#     - The capabilities are:
#         - When payment is received, settlement SHOULD be performed immediately
#         - SHOULD notify payee agent with settlement notification ONLY IF the settlement has proceeded successfully.
#         - If settlement was failed, reply with the status and error message.
#     - Direct settlement-related queries here

# 3. Payee Agent:
#     - For questions about whether received the settlement notification.
#     - The capabilities are:
#         - Receive the settlement notification
#         - Notify the payment initiator
#     - Direct list or get product and payee-related queries here   

# **Interaction History:**
# <interaction_history>
# {interaction_history}
# </interaction_history>

# **Core Capabilities:**

# 1. Query Understanding & Routing
#     - Payer agent create payment by order number set with spend amount, budget, expiration date and currency.
#     - Settlement agent AUTOMATICALLY process this payment created by payer.
#     - Payee make a reply and create the order when received the notification that settlement has finished.

# 2. State Management
#     - Use state to provide personalized responses

# Always maintain a helpful and professional tone.
# DO NOT return 'interaction_history' within message


payment_agent = SequentialAgent(
    name="PaymentAgentPipeline",
    description="Payment agent pipeline for zen7 payment service",
    sub_agents=[payer_agent, settlement_agent, payee_agent]
)

def initialize_payment_or_query_orders(input_message: str, tool_context: ToolContext) -> str:
    if "initialize payment" in input_message:
        print(f"Tool: Detected initializing payment, transfer to payment agent.")
        tool_context.actions.transfer_to_agent = "PaymentAgentPipeline"
        return "Transferring to the payment agent..."
    elif "query order" in input_message:
        print(f"Tool: Detected querying order or get allowance, will transfer to order agent.")
        tool_context.actions.transfer_to_agent = "QueryOrderAgent"
        return "Transferring to the order agent..."
    elif "get allowance" in input_message:
        print(f"Tool: Detected getting allowance, will transfer to allowance agent.")
        tool_context.actions.transfer_to_agent = "QueryAllowanceAgent"
        return "Transferring to the allowance agent..."
    else:
        return f"Processed query: '{input_message}'. No further action needed"

escalation_tool = FunctionTool(func=initialize_payment_or_query_orders)

host_agent = Agent(
    name="GeneralPaymentAgent",
    model="gemini-2.0-flash-lite",
    instruction="""
    You are a helpful assistant help user initialize payment or query orders.
    You capabilities are:
    - Use tool 'initialize_payment_or_query_orders' by identifying intent of the input_message for which indicate initializing a payment, querying order or getting allowance issues.
    - If the input_message mentioned about both order number, spend amount, budget amount, expiration date, currency and chain that indicate to initialize a payment.
    - If the input_message ONLY mentioned order number that indicate to query order.
    - If the input_message ONLY mentioned getting allowance that indicate to get allowance.
    - Immediate make decision, tranfer to the target agent and automatical start the process, DO NOT make any confirmation.
    """,
    tools=[initialize_payment_or_query_orders],
    sub_agents=[payment_agent, order_agent, allowance_agent]
)
