from log import logger
from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext

def receive_notification(tool_context: ToolContext) -> dict[str, any]:
    '''
    Receive settlement notification for payee from settlement agent
    '''
    notification = tool_context.state.get("user:payee_notification")
    if notification:
        logger.info(f"Received notification: {notification} from settlement agent")
        return {
            "status": "success",
            "message": notification
        }
    
    logger.error("None of notification received from settlement agent")
    return {
        "status": "failed",
        "message": "None of notification received from settlement agent"
    }

payee_agent = LlmAgent(
    name="payee_agent",
    model="gemini-2.0-flash-lite",
    description="Payee agent for the zen7 payment to handle payee operations.",
    instruction="""
    You are the payee agent for the zen7 payment to receive notification from settlement agent when finished.
    
    Your capabilities are:
    - Use tool 'receive_notification' to receive notification when settlement has finished.
    - SHOULD keep the order number in return message in order to help user get order detail.
   
    **Interaction History:**
    <interaction_history>
    {interaction_history}
    </interaction_history>
  
    """,
    tools=[receive_notification]
)