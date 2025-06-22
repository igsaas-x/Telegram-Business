from sqlalchemy import Column, Integer, BigInteger
from config.database_config import Base

class RegisteredChat(Base):
    __tablename__ = 'registered_chats'

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, unique=True, nullable=False)

    def __repr__(self):
        return f"<RegisteredChat(chat_id='{self.chat_id}')>"
