import logging
from logging import getLogger, StreamHandler
from fastmcp import FastMCP

import requests
import click
from dotenv import load_dotenv
import os

load_dotenv()

zen7_payment_server_host = os.getenv("ZEN7_PAYMENT_SERVER_HOST")
zen7_payment_server_port = os.getenv("ZEN7_PAYMENT_SERVER_PORT")
zen7_payment_server_base_url = f"http://{zen7_payment_server_host}:{zen7_payment_server_port}"

logger = getLogger(__name__)
logger.addHandler(StreamHandler())
logger.setLevel(level=logging.INFO)

app = FastMCP(name="zen7_payment_mcp")

@app.tool()
async def proceed_payment_and_settlement_and_order_details(message: str, user_id: str = "mcp_user", sign_info: dict = {}, owner_wallet_address: str = "", timezone: str = "") -> dict[str, any]:
    """
    ***Core capabilities***
    1. Do not modify content submitted to the tool "proceed_payment_and_settlement_and_order_details"
    2. The result of the tool "proceed_payment_and_settlement_and_order_details" MUST BE RETURNED AS IS
    3. The returned content SHOULD contain the order number if the response has provided.
    """
    logger.info(f"============= Got user_id from context: {user_id} =============")
    logger.info(f"============= Got sign_info from context: {sign_info} =============")
    logger.info(f"============= Got owner_wallet_address from context: {owner_wallet_address} =============")
    logger.info(f"============= Got timezone from context: {timezone} =============")
    res = requests.post(f"{zen7_payment_server_base_url}/chat_a2a", json={"message": message, "user_id": user_id, "sign_info": sign_info, "owner_wallet_address": owner_wallet_address, "timezone": timezone})
    if res.ok:
        data = res.json()
        message = data["response"]
        logger.info(f"{message["event"]["author"].capitalize()}: {message["final_response"]}")
        return {"message": message}
    return {"message": ""}

@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=8015)
def main(host, port):
    print(f"Zen7 Payment Server is running at {zen7_payment_server_base_url}/chat_a2a")
    app.run(transport="sse", host=host, port=port)

if __name__ == "__main__":
    main()
    