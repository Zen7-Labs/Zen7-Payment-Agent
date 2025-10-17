from log import logger

from google.adk.runners import Runner
from google.adk.events import Event

from google.genai import types

from datetime import datetime

import pytz
from tzlocal import get_localzone

class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

async def update_interaction_history(session_service, app_name: str, user_id: str, session_id: str, entry: dict[str, any]):
    """
    Add an entry to the interaction history in state.

    Args:
        session_service: The session service instance
        app_name: The application name
        user_id: The user ID
        session_id: The session ID
        entry: A dictionary containing the state data
            - requires 'action' key (e.g., 'user_query', 'agent_response')
            - other keys are flexible depending on the action type
    """
    try:
        session = await session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)        
        interaction_history = session.state.get("interaction_history", [])
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        interaction_history.append(entry)
        
        updated_state = session.state.copy()
        updated_state["interaction_history"] = interaction_history

        await session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            state=updated_state
        )

    except Exception as e:
        logger.error(f"Error updating interaction history: {e}")

async def add_user_query_to_history(session_service, app_name: str, user_id: str, session_id: str, query: dict[str, any]):
    """Add a user query to the interaction history."""
    await update_interaction_history(
        session_service,
        app_name,
        user_id,
        session_id,
        {
            "action": "user_query",
            "query": query
        }
    )

async def add_agent_response_to_history(session_service, app_name: str, user_id: str, session_id: str, agent_name: str, response: any):
    """Add an agent response to the interaction history."""
    await update_interaction_history(
        session_service,
        app_name,
        user_id,
        session_id,
        {
            "action": "agent_response",
            "agent": agent_name,
            "response": response
        }
    )

async def display_state(session_service, app_name: str, user_id: str, session_id: str, label: str = "Current State"):
    """Display the current session state in a formatted way."""
    try:
        session = await session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
        logger.info(f"\n{'-' * 10}{label}{'-' * 10}")
        
        interaction_history = session.state.get("interaction_history", [])
        if interaction_history:
            logger.info(" Interaction History:")
            for idx, interaction in enumerate(interaction_history, 1):
                if isinstance(interaction, dict):
                    action = interaction.get("action", "interaction")
                    timestamp = interaction.get("timestamp", "unknown time")
                    if action == "user_query":
                        query = interaction.get("query", "")
                        logger.info(f"  {idx}. User query at {timestamp}: {query}")
                    elif action == "agent_response":
                        agent = interaction.get("agent", "unknown")
                        response = interaction.get("response", "")
                        if len(response) > 100:
                            response = response[:97] + "..."
                        logger.info(f' {idx}. {agent} response at {timestamp}: "{response}"')  
                    else:
                        details = ", ".join(f"{k}: {v}" for k, v in interaction.items() if k not in ["action", "timestamp"])
                        logger.info(f" {idx}. {action} at {timestamp}" + "({details})" if details else "")
        else:
            logger.info(" Interaction History: None")
    except Exception as e:
        logger.error(f"Failed to display current session: {e}")

async def process_agent_response(event: Event) -> dict[str, any]:
    """Process and display agent response events."""
    resp_body = {
        "event": {
            "id": event.id,
            "author": event.author
        },
        "content": [],
        "final_response": None
    }
    logger.info(f"Event ID: {event.id}, Author: {event.author}")
    if event.content and event.content.parts:
        for part in event.content.parts:
            if hasattr(part, "text") and part.text and not part.text.isspace():
                logger.info(f"  Text: '{part.text.strip()}'")
                resp_body["content"].append(part.text.strip())
    final_response = None
    if event.is_final_response():
        if (event.content and event.content.parts and hasattr(event.content.parts[0], "text") and event.content.parts[0].text):
            final_response = event.content.parts[0].text.strip()
            logger.info(f"\n{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD}==== AGENT RESPONSE ==============={Colors.RESET}")
            logger.info(f"{Colors.CYAN}{Colors.BOLD}{final_response}{Colors.RESET}")
            logger.info(f"{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD}==================================={Colors.RESET}")
        else:
            logger.info(f"\n{Colors.BG_RED}{Colors.WHITE}{Colors.BOLD}==> Final Agent Response: [No text content in final event]{Colors.RESET}\n")
        resp_body["final_response"] = final_response
    return resp_body

async def call_agent_async(runner: Runner, user_id: str, session_id: str, query: str) -> dict[str, any]:
    """Call the agent asynchronously with the user's query."""
    content = types.Content(role="user", parts=[types.Part(text=query)])
    logger.info(f"\n{Colors.BG_GREEN}{Colors.BLACK}{Colors.BOLD}--- Running Query: {query} ---{Colors.RESET}")

    final_response_text = None
    agent_name = None
    resp_body = None
    # await display_state(runner.session_service, runner.app_name, user_id, session_id, "State BEFORE processing")
    try:
        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
            if event.author:
                agent_name = event.author
            if event.is_final_response():
                if event.content and event.content.parts:
                    logger.info(f"Final Response: {event.content.parts[0].text}")
            
            resp_body = await process_agent_response(event)
            if resp_body["final_response"]:
               final_response_text = resp_body["final_response"]
                
    except Exception as e:
        logger.error(f"Error during agent run: {e}")

    if final_response_text and agent_name:
        await add_agent_response_to_history(
            runner.session_service,
            runner.app_name,
            user_id,
            session_id,
            agent_name,
            final_response_text
        )
    # await display_state(runner.session_service, runner.app_name, user_id, session_id, "State AFTER processing")
    logger.info(f"{Colors.YELLOW}{'-' * 30}{Colors.RESET}")
    return resp_body

def is_valid_date_format(date_string, date_format='%Y-%m-%d'):
    """
    Checks if a given string matches the specified date format.

    Args:
        date_string (str): The string to validate.
        date_format (str): The expected date format (default: '%Y-%m-%d').

    Returns:
        bool: True if the string is a valid date in the given format, False otherwise.
    """
    try:
        # Attempt to parse the string into a datetime object
        datetime.strptime(date_string, date_format)
        return True
    except ValueError:
        # If parsing fails, strptime raises a ValueError, indicating an invalid format or date
        return False
    
def convert_to_local_timezone(dt: datetime, source_tz: str = "Asia/Shanghai") -> datetime:
    """
    Converts a single datetime object from a source timezone to the local 
    timezone of the machine running the code.

    Args:
        dt: The datetime object to convert (should be naive).
        source_tz: The timezone string (e.g., 'America/New_York') for dt.

    Returns:
        A timezone-aware datetime object in the local system's timezone.
    """
    # 1. Define the source and target timezone objects
    source_timezone = pytz.timezone(source_tz)
    target_timezone = get_localzone() 
    
    logger.info(f"Target Timezone automatically detected: {target_timezone}")

    # 2. Localize the naive datetime to its source timezone
    # .localize() handles Daylight Saving Time (DST) transitions correctly
    aware_dt = source_timezone.localize(dt)
    
    # 3. Convert the aware datetime to the target (local) timezone
    converted_dt = aware_dt.astimezone(target_timezone)

    return converted_dt