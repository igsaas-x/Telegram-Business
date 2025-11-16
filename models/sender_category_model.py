import typing

if typing.TYPE_CHECKING:
    from models.sender_config_model import SenderConfig

from sqlalchemy import Boolean, Integer, String, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base_model import BaseModel


class SenderCategory(BaseModel):
    """
    Represents a category for grouping senders in reports.

    Examples:
        - VIP Customers
        - Pay Later
        - Cash on Delivery
        - Delivery Partners
    """
    __tablename__ = "sender_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    category_name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    senders: Mapped[list["SenderConfig"]] = relationship(
        "SenderConfig",
        back_populates="category"
    )
