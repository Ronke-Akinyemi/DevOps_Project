from sqlmodel import create_engine, SQLModel, Session
from sqlalchemy.ext.automap import automap_base

from utils.config import DATABASE_URL
import logging

logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)


engine = create_engine(DATABASE_URL, echo=True)
AutomapBase = automap_base()



def init_db():
    # Reflect existing tables into metadata
    AutomapBase.prepare(engine, reflect=True)
    # Create new tables if they don't exist
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session