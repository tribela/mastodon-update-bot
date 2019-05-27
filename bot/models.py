from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from typing import TypeVar

T = TypeVar('T')

Base = declarative_base()


def get_or_create(session, model: T, **kwargs: dict) -> (T, bool):
    """Get or create
    :return: (instance: model, is_created: bool)
    """
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False

    instance = model(**kwargs)
    session.add(instance)
    session.commit()
    return instance, True


class Mastodon(Base):
    __tablename__ = 'mastodon'

    id = Column(Integer, primary_key=True)
    version = Column(String, nullable=False)
    updated = Column(DateTime(timezone=True))

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.version} {self.updated}>'


class Server(Base):

    __tablename__ = 'servers'

    domain = Column(String, primary_key=True)
    version = Column(String)
    last_fetched = Column(DateTime(timezone=True))
    last_notified = Column(DateTime(timezone=True))

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.domain} {self.version} ({self.last_fetched})>'


class Admin(Base):

    __tablename__ = 'admins'

    acct = Column(String, primary_key=True)
    domain = Column(String, ForeignKey(Server.domain))
    server = relationship(Server, backref='admins')

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.acct}>'
