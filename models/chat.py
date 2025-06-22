from sqlalchemy import Column, Integer, String

from config.database_config import Base, SessionLocal


class Chat(Base):
    __tablename__ = 'chats'
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(255), unique=True, nullable=False)

class ChatService:
    def __init__(self):
        self.Session = SessionLocal

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

    def get_all_chat_ids(self):
        session = self.Session()
        try:
            chats = session.query(Chat.chat_id).all()
            return [int(c[0]) for c in chats]
        except Exception as e:
            print(f"Error fetching chat IDs: {e}")
            return []
        finally:
            session.close()
