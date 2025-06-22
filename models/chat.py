from sqlalchemy import create_engine, Column, Integer, String, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

Base = declarative_base()

class Chat(Base):
    __tablename__ = 'chats'
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(255), unique=True, nullable=False)

class ChatService:
    def __init__(self):
        db_url = f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)  # Create table if it doesn't exist
        self.Session = sessionmaker(bind=self.engine)

    def register_chat_id(self, chat_id):
        session = self.Session()
        try:
            # Check if chat_id already exists
            existing_chat = session.query(Chat).filter_by(chat_id=str(chat_id)).first()
            if existing_chat:
                return False, f"Chat ID {chat_id} is already registered."

            # Insert new chat_id
            new_chat = Chat(chat_id=str(chat_id))
            session.add(new_chat)
            session.commit()
            return True, f"Chat ID {chat_id} registered successfully."
        except Exception as e:
            session.rollback()
            return False, f"Error registering chat ID: {e}"
        finally:
            session.close()
