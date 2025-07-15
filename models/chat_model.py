import typing

if typing.TYPE_CHECKING:
    from models.user_model import User

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    BigInteger,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base_model import BaseModel


class Chat(BaseModel):
    __tablename__ = "chat_group"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    group_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=True, default=True)
    enable_shift: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    user: Mapped["User"] = relationship("User", back_populates="chats")
