import typing

if typing.TYPE_CHECKING:
    from models.sender_category_model import SenderCategory

from sqlalchemy import Boolean, Integer, String, BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base_model import BaseModel


class SenderConfig(BaseModel):
    __tablename__ = "sender_configs"

    __table_args__ = (
        UniqueConstraint(
            'chat_id',
            'sender_account_number',
            'sender_name',
            name='unique_sender_per_chat'
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sender_account_number: Mapped[str] = mapped_column(String(3), nullable=False)
    sender_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Category and nickname fields
    category_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("sender_categories.id", ondelete="SET NULL"),
        nullable=True
    )
    nickname: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    # Relationships
    category: Mapped["SenderCategory | None"] = relationship(
        "SenderCategory",
        back_populates="senders"
    )

    def get_display_name(self) -> str:
        """
        Get display name with priority: nickname → sender_name → *{sender_account_number}

        Returns:
            Display name for this sender

        Examples:
            >>> sender = SenderConfig(sender_account_number="708", sender_name="John Doe", nickname="Johnny")
            >>> sender.get_display_name()
            'Johnny'
            >>> sender.nickname = None
            >>> sender.get_display_name()
            'John Doe'
            >>> sender.sender_name = None
            >>> sender.get_display_name()
            '*708'
        """
        if self.nickname:
            return self.nickname
        if self.sender_name:
            return self.sender_name
        return f"*{self.sender_account_number}"
