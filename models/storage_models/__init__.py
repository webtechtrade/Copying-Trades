from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


class DeclarativeBase:
    pass


DeclarativeBase = declarative_base(cls=DeclarativeBase)

