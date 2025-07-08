from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Enum as SQLAlchemyEnum,
)
from sqlalchemy.orm import Session, relationship
from contextlib import contextmanager
from typing import Generator, Any
from config.database_config import SessionLocal
from models.base_model import BaseModel


class ServicePackage(Enum):
    BASIC = "BASIC"
    PRO = "PRO"
    UNLIMITED = "UNLIMITED"


class User(BaseModel):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    first_name = Column(String(50), unique=True, nullable=False)
    last_name = Column(String(50), unique=True, nullable=False)
    identifier = Column(String(50), unique=True, nullable=False)
    phone_number = Column(String(20), unique=True, nullable=True)
    is_paid = Column(Boolean, default=False)
    package = Column(
        SQLAlchemyEnum(ServicePackage), nullable=False, default=ServicePackage.BASIC
    )
    is_active = Column(Boolean, default=True)
    chats = relationship("Chat", back_populates="user")


class UserService:
    def __init__(self):
        self._session_factory = SessionLocal

    @contextmanager
    def _get_db(self) -> Generator[Session, Any, Any]:
        db = self._session_factory()
        try:
            yield db
        finally:
            db.close()

    async def update_user_package(
        self, user_identifier: str, package: ServicePackage
    ) -> User | None:
        with self._get_db() as db:
            user = db.query(User).filter(User.identifier == user_identifier).first()
            if user:
                user.package = package.value  # type: ignore
                db.commit()
                return user
            return None

    async def get_user_by_identifier(self, identifier: str) -> User:
        with self._get_db() as db:
            user = db.query(User).filter(User.identifier == identifier).first()
            return user

    async def create_user(self, sender) -> User:
        user = User(
            first_name=sender.first_name,
            last_name=sender.last_name,
            phone_number=sender.phone,
            identifier=sender.id,
            username=sender.username,
            is_paid=False,
            package=ServicePackage.BASIC,
            is_active=False,
        )

        with self._get_db() as db:
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
