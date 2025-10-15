import typing
from datetime import datetime

if typing.TYPE_CHECKING:
    from models.chat_model import Chat

from sqlalchemy import (
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base_model import BaseModel


class CustomReport(BaseModel):
    __tablename__ = "custom_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_group_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chat_group.id", ondelete="CASCADE"), nullable=False
    )
    report_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sql_query: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    schedule_time: Mapped[str | None] = mapped_column(
        String(5), nullable=True
    )  # Format: "HH:MM"
    schedule_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationship to chat_group
    chat_group: Mapped["Chat"] = relationship("Chat", backref="custom_reports")
