from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


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
