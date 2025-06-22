from datetime import datetime

from sqlalchemy import String, Column, Integer, DateTime, Boolean, BigInteger

from config.database_config import Base, SessionLocal


class BotQuestion(Base):
    __tablename__ = 'bot_questions'
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, nullable=False)  # Using BigInteger for Telegram chat IDs
    message_id = Column(Integer, nullable=False)
    question_type = Column(String(32), nullable=False)  # e.g., 'date_input', 'amount_input', etc.
    is_replied = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Optional - store context data as JSON if needed
    context_data = Column(String(512), nullable=True)

class ConversationService:
    def __init__(self):
        self.db = SessionLocal()

    async def save_question(self, chat_id: int, message_id: int, question_type: str, context_data: str = None):
        """Save a new question to track"""
        try:
            new_question = BotQuestion(
                chat_id=chat_id,
                message_id=message_id,
                question_type=question_type,
                context_data=context_data
            )
            self.db.add(new_question)
            self.db.commit()
            return new_question
        except Exception as e:
            self.db.rollback()
            raise e

    async def mark_as_replied(self, chat_id: int, message_id: int):
        """Mark a question as replied"""
        try:
            question = self.db.query(BotQuestion).filter(
                BotQuestion.chat_id == chat_id,
                BotQuestion.message_id == message_id,
                BotQuestion.is_replied == False
            ).first()
            
            if question:
                question.is_replied = True
                question.updated_at = datetime.now()
                self.db.commit()
                return question
            return None
        except Exception as e:
            self.db.rollback()
            raise e

    async def get_pending_question(self, chat_id: int, question_type: str = None):
        """Get the most recent pending question for a chat"""
        query = self.db.query(BotQuestion).filter(
            BotQuestion.chat_id == chat_id,
            BotQuestion.is_replied == False
        )
        
        if question_type:
            query = query.filter(BotQuestion.question_type == question_type)
            
        return query.order_by(BotQuestion.created_at.desc()).first()

    async def get_question_by_message_id(self, chat_id: int, message_id: int):
        """Get a question by its message ID"""
        return self.db.query(BotQuestion).filter(
            BotQuestion.chat_id == chat_id,
            BotQuestion.message_id == message_id
        ).first()
        
    def __del__(self):
        self.db.close()
