import os
from typing import Generator, Any
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from config import load_environment

load_environment()
DATABASE_URL = (
    f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
)

engine = create_engine(
    DATABASE_URL, pool_size=5, max_overflow=10, pool_timeout=30, pool_recycle=1800
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class DatabaseSession:
    """A database session context manager"""

    def __init__(self):
        self.db = SessionLocal()

    def __enter__(self) -> Session:
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()


def get_db_session() -> DatabaseSession:
    """Get a database session using a context manager.

    Usage:
        with get_db() as db:
            result = db.query(Model).filter(Model.id == 1).first()
    """
    return DatabaseSession()


def create_db_tables():
    # Base.metadata.create_all(bind=engine)
    pass