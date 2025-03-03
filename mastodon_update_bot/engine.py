from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base


def get_session(url: str):
    engine = create_engine(url)
    session = sessionmaker(engine)

    return session


def init_db(url: str):
    engine = create_engine(url)
    Base.metadata.create_all(engine)
