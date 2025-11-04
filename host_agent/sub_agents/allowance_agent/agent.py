from log import logger
from google.adk.agents import Agent
from google.adk.tools import ToolContext

from dotenv import load_dotenv
import os
import json

load_dotenv()

settlement_mode = os.getenv("SETTLEMENT_MODE")

if settlement_mode == "CUSTODIAL":
    from services.custodial.transfer_handler import create_sepolia_handler
if settlement_mode == "NONE_CUSTODIAL":
    from services.non_custodial.execute_permit import create_handler

async def get_allowance(owner_wallet_address: str, tool_context: ToolContext) -> dict[str, any]:
    wallet_address = None
    if owner_wallet_address:
        wallet_address = owner_wallet_address
    else:
        wallet_address = tool_context.state.get("owner_wallet_address")
        logger.info(f"Get wallet address from context: {wallet_address}")
    if wallet_address:
        logger.info(f"Get allowance for wallet address: {wallet_address}")
        payment_info = tool_context.state.get("payment_info")
        chain, currency = None, None
        if "chain" in payment_info:
            chain = payment_info["chain"]
        if "currency" in payment_info:
            currency = payment_info["currency"]
        if not (chain or currency):
            logger.error(f"None of chain or currency configured.")
            return {
                "status": "failed",
                "message": "None of chain or currency configured."
            }
        logger.info(f"Get allowance for chain: {chain}, currency: {currency}")
        handler = create_handler(network=chain, token=currency)    
        result = await handler.check_allowance(owner_address=wallet_address)
        return {
            "status": "success",
            "message": {
                "allowance": result["allowance"],
                "owner_wallet_address": result["owner"]
            }
        }
    return {
        "status": "failed",
        "message": "None of owner_wallet_address found."
    }

allowance_agent = Agent(
    name="QueryAllowanceAgent",
    model="gemini-2.0-flash-lite",
    instruction="""
        Your goal is help user get allowance by owner wallet address.

        Your responsibilites are:
        - Use tool 'get_allowance' to get allowance by owner wallet address, MUST return in JSON format.
          e.g. 
          {
            "allowance": <allowance>,
            "owner_wallet_address": <owner>
          }
          
    """,
    tools=[get_allowance]
)