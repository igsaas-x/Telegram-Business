from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, joinedload

from config.database_config import Base, SessionLocal
from models import User, IncomeService, ServicePackage


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
        self.income_service = IncomeService()

    async def is_unlimited_package(self, chat_id: str) -> int | None:
        try:
            chat = await self.get_chat_by_chat_id(chat_id)
            if chat and chat.enable_shift and chat.user.package == ServicePackage.UNLIMITED:  # type: ignore
                last_shift = await self.income_service.get_last_shift_id(chat_id)
                return last_shift.shift if last_shift else None  # type: ignore
        except Exception as e:
            print(f"Error checking unlimited package: {e}")

    async def register_chat_id(self, chat_id, group_name, user: User | None):
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

    async def update_chat_enable_shift(self, chat_id: str, enable_shift: bool):
        session = self.Session()
        try:
            session.query(Chat).filter_by(chat_id=str(chat_id)).update(
                {"enable_shift": enable_shift}
            )
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error updating chat enable_shift: {e}")
            return False
        finally:
            session.close()

    async def update_chat_status(self, chat_id: str, status: bool):
        session = self.Session()
        try:
            session.query(Chat).filter_by(chat_id=chat_id).update({"is_active": status})
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error updating chat status: {e}")
            return False
        finally:
            session.close()

    async def update_chat_user_id(self, chat_id: str, user_id: int):
        session = self.Session()
        try:
            session.query(Chat).filter_by(chat_id=chat_id).update({"user_id": user_id})
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error updating chat user_id: {e}")
            return False
        finally:
            session.close()

    async def get_chat_by_chat_id(self, chat_id: str) -> Chat | None:
        session = self.Session()
        try:
            chat = session.query(Chat).options(joinedload(Chat.user)).filter_by(chat_id=chat_id).first()
            return chat
        except Exception as e:
            print(f"Error fetching chat by chat ID: {e}")
            return None
        finally:
            session.close()

    async def get_all_chat_ids(self):
        session = self.Session()
        try:
            chats = session.query(Chat.chat_id).all()
            return [int(c[0]) for c in chats]
        except Exception as e:
            print(f"Error fetching chat IDs: {e}")
            return []
        finally:
            session.close()

    async def is_shift_enabled(self, chat_id: str) -> bool:
        try:
            chat = await self.get_chat_by_chat_id(chat_id)
            return chat.enable_shift if chat else False
        except Exception as e:
            print(f"Error checking shift enabled: {e}")
            return False
