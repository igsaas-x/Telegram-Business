from enum import Enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Enum as SQLAlchemyEnum,
)
from sqlalchemy.orm import relationship

from models.base_model import BaseModel
from config.database_config import get_db_session


class ServicePackage(Enum):
    BASIC = "BASIC"
    PRO = "PRO"
    UNLIMITED = "UNLIMITED"


class User(BaseModel):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    identifier = Column(String(50), unique=True, nullable=False)
    phone_number = Column(String(20), unique=True, nullable=True)
    is_paid = Column(Boolean, default=False)
    package = Column(
        SQLAlchemyEnum(ServicePackage), nullable=False, default=ServicePackage.BASIC
    )
    is_active = Column(Boolean, default=True)
    chats = relationship("Chat", back_populates="user")


class UserService:
    """User service"""

    async def update_user_package(
        self, user_identifier: str, package: ServicePackage
    ) -> User | None:
        """Update user package"""
        with get_db_session() as db:
            user = db.query(User).filter(User.identifier == user_identifier).first()
            if user:
                user.package = package  # type: ignore
                db.commit()
                return user
            return None

    async def get_user_by_identifier(self, identifier: str) -> type[User] | None:
        """Get user by identifier"""
        with get_db_session() as db:
            user = db.query(User).filter(User.identifier == identifier).first()
            return user

    async def get_user_by_username(self, username: str) -> type[User] | None:
        """Get user by username"""
        with get_db_session() as db:
            user = db.query(User).filter(User.username == username).first()
            return user

    async def create_user(self, sender) -> User | type[User]:
        """Create user"""
        # First check if user already exists by identifier or username
        with get_db_session() as db:
            existing_user = (
                db.query(User)
                .filter(
                    (User.identifier == sender.id) | (User.username == sender.username)
                )
                .first()
            )

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
                is_paid=False,
                package=ServicePackage.BASIC,
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
