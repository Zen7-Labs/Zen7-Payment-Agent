import logging

import click
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from agent import process_with_content_agent
from agent_executor import ADKAgentExecutor

from dotenv import load_dotenv
import os

load_dotenv()

zen7_payment_server_host = os.getenv("ZEN7_PAYMENT_SERVER_HOST")
zen7_payment_server_port = os.getenv("ZEN7_PAYMENT_SERVER_PORT")
zen7_payment_server_base_url = f"http://{zen7_payment_server_host}:{zen7_payment_server_port}"


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MissingAPIKeyError(Exception):
    """Exception for missing API key."""

@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=10000)
def main(host, port):

    # Agent card (metadata)
    agent_card = AgentCard(
        name='Process with provided content',
        description=process_with_content_agent.description,
        url=f'http://{host}:{port}',
        version="1.0.0",
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="process_with_content",
                name="process_with_content",
                description=process_with_content_agent.description,
                tags=["process", "content"],
                examples=[]
            )
        ],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=ADKAgentExecutor(
            agent=process_with_content_agent,
        ),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )

    uvicorn.run(server.build(), host=host, port=port)


if __name__ == "__main__":
    logger.info(f"Zen7 Payment Server is running at {zen7_payment_server_base_url}/chat_a2a")
    main()