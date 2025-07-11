from contextlib import contextmanager
from enum import Enum
from typing import Optional, Union

from sqlalchemy import String, Column, Integer, DateTime, Boolean, BigInteger

from helper.dateutils import DateUtils
from models.base_model import BaseModel
from config import get_db


class QuestionType(Enum):
    DATE_INPUT = "date_input"
    AMOUNT_INPUT = "amount_input"


class BotQuestion(BaseModel):
    __tablename__ = "bot_questions"

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, nullable=False)
    message_id = Column(Integer, nullable=False)
    question_type = Column(String(32), nullable=False)
    is_replied = Column(Boolean, default=False)
    created_at = Column(DateTime, default=DateUtils.now)
    updated_at = Column(DateTime, default=DateUtils.now, onupdate=DateUtils.now)
    context_data = Column(String(512), nullable=True)

    def mark_as_replied(self) -> None:
        self.is_replied = True
        self.updated_at = DateUtils.now()


class ConversationService:
    def __init__(self):
        self._session_factory = get_db

    async def save_question(
        self,
        chat_id: int,
        message_id: int,
        question_type: Union[QuestionType, str],
        context_data: Optional[str] = None,
    ) -> BotQuestion:
        with self._session_factory() as session:
            question_type_value = (
                question_type.value
                if isinstance(question_type, QuestionType)
                else question_type
            )
            new_question = BotQuestion(
                chat_id=chat_id,
                message_id=message_id,
                question_type=question_type_value,
                context_data=context_data,
            )
            session.add(new_question)
            return new_question

    async def mark_as_replied(
        self, chat_id: int, message_id: int
    ) -> type[BotQuestion] | None:
        with self._session_factory() as session:
            question = (
                session.query(BotQuestion)
                .filter(
                    BotQuestion.chat_id == chat_id,
                    BotQuestion.message_id == message_id,
                    BotQuestion.is_replied == False,  # type: ignore
                )
                .first()
            )

            if question:
                question.mark_as_replied()
                return question  # type: ignore
            return None

    async def get_pending_question(
        self, chat_id: int, question_type: Optional[QuestionType] = None
    ) -> Optional[BotQuestion]:
        with self._session_factory() as session:
            query = session.query(BotQuestion).filter(
                BotQuestion.chat_id == chat_id, BotQuestion.is_replied == False  # type: ignore
            )

        if question_type:
            query = query.filter(BotQuestion.question_type == question_type.value)

        return query.order_by(BotQuestion.created_at.desc()).first()

    async def get_question_by_message_id(
        self, chat_id: int, message_id: int
    ) -> Optional[BotQuestion]:
        with self._session_factory() as session:
            return (
                session.query(BotQuestion)
                .filter(
                    BotQuestion.chat_id == chat_id, BotQuestion.message_id == message_id
                )
                .first()
            )
