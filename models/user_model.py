from sqlalchemy import (
    Integer,
    String,
    Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base_model import BaseModel
from models.chat_model import Chat


class User(BaseModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    identifier: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    phone_number: Mapped[str | None] = mapped_column(
        String(20), unique=True, nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    chats: Mapped[list[Chat]] = relationship("Chat", back_populates="user")
