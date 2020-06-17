from injector import Injector
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from configuration import Configuration
from models.storage_models import DeclarativeBase


class StorageService:
    def __init__(self):
        configuration = Configuration()
        self.database = configuration.config['DEFAULT']['DATABASE']
        self.sessions = {}

        self.engine = self.create_engine()
        self.create_tables(self.engine)

    def create_engine(self):
        engine = create_engine(URL(**self.database), poolclass=NullPool, encoding="utf8",
                               connect_args={'check_same_thread': False})
        return engine

    def create_tables(self, engine):
        DeclarativeBase.metadata.create_all(engine, checkfirst=True)

    def create_session(self):
        session = sessionmaker(bind=self.engine)()
        return session
