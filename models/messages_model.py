"""Messages model for the database and its operations"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.sql import expression
from typing import List, Optional
from models.base_model import BaseModel
from config import get_db_session


class MessagesModel(BaseModel):
    """Messages model"""

    __tablename__ = "messages"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
        server_default=expression.text("1"),
    )
    chat_id = Column(String(255), nullable=False)
    message_id = Column(String(255), nullable=False)
    original_message = Column(Text, nullable=False)

    def save(self, chat_id: int, message_id: int, original_message: str) -> None:
        """Save the message to the database

        Args:
            chat_id: The chat ID (must be an integer)
            message_id: The message ID
            original_message: The original message text
        """
        with get_db_session() as db:
            self.chat_id = chat_id
            self.message_id = message_id
            self.original_message = original_message
            self.created_at = datetime.now()
            self.updated_at = datetime.now()
            db.add(self)
            db.commit()

    def get_by_message_id(self, message_id: int) -> Optional["MessagesModel"]:
        """Get a message by message_id"""
        with get_db_session() as db:
            return db.query(MessagesModel).filter_by(message_id=message_id).first()

    def get_by_chat_id(self, chat_id: int) -> List["MessagesModel"]:
        """Get all messages by chat_id"""
        with get_db_session() as db:
            return (
                db.query(MessagesModel)
                .filter_by(chat_id=chat_id)
                .order_by(MessagesModel.created_at.desc())
                .all()
            )
