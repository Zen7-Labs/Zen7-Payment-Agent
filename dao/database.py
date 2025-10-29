from log import logger
from . import db_url

from sqlmodel import create_engine, SQLModel

engine = create_engine(db_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    logger.info(f"Successfully created db and tables.")