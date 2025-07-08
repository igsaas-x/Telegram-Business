from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship

from config.database_config import Base, SessionLocal
from models.user_model import User


class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(255), unique=True, nullable=False)
    group_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=True, default=False)
    enable_shift = Column(Boolean, nullable=True, default=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="chats")


class ChatService:
    def __init__(self):
        self.Session = SessionLocal

    def register_chat_id(self, chat_id, group_name, user: User | None):
        session = self.Session()
        try:
            new_chat = Chat(
                chat_id=str(chat_id),
                group_name=group_name,
                user_id=user.id if user else None,
            )
            session.add(new_chat)
            session.commit()
            return True, f"Chat ID {chat_id} registered successfully."
        except Exception as e:
            session.rollback()
            return False, f"Error registering chat ID: {e}"
        finally:
            session.close()

    def update_chat_enable_shift(self, chat_id: str, enable_shift: bool):
        session = self.Session()
        try:
            session.query(Chat).filter_by(chat_id=str(chat_id)).update(
                {"enable_shift": enable_shift}
            )
            session.commit()
        except Exception as e:
            session.rollback()
        finally:
            session.close()

    def update_chat_status(self, chat_id: str, status: bool):
        session = self.Session()
        try:
            session.query(Chat).filter_by(chat_id=chat_id).update({"is_active": status})
            session.commit()
        except Exception as e:
            session.rollback()
        finally:
            session.close()

    def get_chat_by_chat_id(self, chat_id: str) -> Chat | None:
        session = self.Session()
        try:
            return session.query(Chat).filter_by(chat_id=chat_id).first()
        except Exception as e:
            print(f"Error fetching chat by chat ID: {e}")

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
