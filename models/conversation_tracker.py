from contextlib import contextmanager
from datetime import datetime
from enum import Enum
from typing import Optional, Union

from sqlalchemy import String, Column, Integer, DateTime, Boolean, BigInteger
from sqlalchemy.orm import Session

from config.database_config import Base, SessionLocal


class QuestionType(Enum):
    DATE_INPUT = "date_input"
    AMOUNT_INPUT = "amount_input"

class BotQuestion(Base):
    __tablename__ = 'bot_questions'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, nullable=False)
    message_id = Column(Integer, nullable=False)
    question_type = Column(String(32), nullable=False)
    is_replied = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    context_data = Column(String(512), nullable=True)

    def mark_as_replied(self) -> None:
        self.is_replied = True
        self.updated_at = datetime.now()

class ConversationService:
    def __init__(self, db_session: Optional[Session] = None):
        self._db = db_session or SessionLocal()

    @contextmanager
    def session_scope(self):
        try:
            yield self._db
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise
        finally:
            self._db.close()

    async def save_question(
        self, 
        chat_id: int, 
        message_id: int, 
        question_type: Union[QuestionType, str],
        context_data: Optional[str] = None
    ) -> BotQuestion:
        with self.session_scope() as session:
            question_type_value = question_type.value if isinstance(question_type, QuestionType) else question_type
            new_question = BotQuestion(
                chat_id=chat_id,
                message_id=message_id,
                question_type=question_type_value,
                context_data=context_data
            )
            session.add(new_question)
            return new_question

    async def mark_as_replied(self, chat_id: int, message_id: int) -> type[BotQuestion] | None:
        with self.session_scope() as session:
            question = session.query(BotQuestion).filter(
                BotQuestion.chat_id == chat_id,
                BotQuestion.message_id == message_id,
                BotQuestion.is_replied == False
            ).first()
            
            if question:
                question.mark_as_replied()
                return question
            return None

    async def get_pending_question(
        self, 
        chat_id: int, 
        question_type: Optional[QuestionType] = None
    ) -> Optional[BotQuestion]:
        query = self._db.query(BotQuestion).filter(
            BotQuestion.chat_id == chat_id,
            BotQuestion.is_replied == False
        )
        
        if question_type:
            query = query.filter(BotQuestion.question_type == question_type.value)
            
        return query.order_by(BotQuestion.created_at.desc()).first()

    async def get_question_by_message_id(
        self, 
        chat_id: int, 
        message_id: int
    ) -> Optional[BotQuestion]:
        return self._db.query(BotQuestion).filter(
            BotQuestion.chat_id == chat_id,
            BotQuestion.message_id == message_id
        ).first()
