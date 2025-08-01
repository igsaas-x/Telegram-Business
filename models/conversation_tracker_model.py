from sqlalchemy import String, Integer, Boolean, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from models.base_model import BaseModel


class BotQuestion(BaseModel):
    __tablename__ = "bot_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_id: Mapped[int] = mapped_column(Integer, nullable=False)
    question_type: Mapped[str] = mapped_column(String(32), nullable=False)
    is_replied: Mapped[bool] = mapped_column(Boolean, default=False)
    context_data: Mapped[str | None] = mapped_column(String(512), nullable=True)

    def mark_as_replied(self):
        """Mark this question as replied"""
        self.is_replied = True
