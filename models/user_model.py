from contextlib import contextmanager
from typing import Generator, Any

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
)
from sqlalchemy.orm import Session, relationship

from config.database_config import SessionLocal
from models.base_model import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    identifier = Column(String(50), unique=True, nullable=False)
    phone_number = Column(String(20), unique=True, nullable=True)
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


    async def get_user_by_identifier(self, identifier: str) -> type[User] | None:
        with self._get_db() as db:
            user = db.query(User).filter(User.identifier == identifier).first()
            return user

    async def get_user_by_username(self, username: str) -> type[User] | None:
        with self._get_db() as db:
            user = db.query(User).filter(User.username == username).first()
            return user

    async def create_user(self, sender) -> User | type[User]:
        # First check if user already exists by identifier or username
        with self._get_db() as db:
            existing_user = db.query(User).filter(
                (User.identifier == sender.id) | (User.username == sender.username)
            ).first()
            
            # If user already exists, return it
            if existing_user:
                return existing_user
        
            # Create new user if not exists
            user = User(
                first_name=sender.first_name,
                last_name=sender.last_name,
                phone_number=sender.phone,
                identifier=sender.id,
                username=sender.username,
                is_active=False,
            )

            try:
                db.add(user)
                db.commit()
                db.refresh(user)
                return user
            except Exception as e:
                db.rollback()
                raise e
