import typing

if typing.TYPE_CHECKING:
    pass

from sqlalchemy import Boolean, Integer, String, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from models.base_model import BaseModel


class SenderConfig(BaseModel):
    __tablename__ = "sender_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sender_account_number: Mapped[str] = mapped_column(String(3), nullable=False)
    sender_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
