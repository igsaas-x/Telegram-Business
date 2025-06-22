from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models.registered_chat import RegisteredChat, Base
import os

class RegistrationService:
    def __init__(self):
        db_url = f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    async def register_chat(self, chat_id):
        session = self.Session()
        try:
            existing_chat = session.query(RegisteredChat).filter_by(chat_id=chat_id).first()
            if existing_chat:
                return False  # Already registered
            
            new_chat = RegisteredChat(chat_id=chat_id)
            session.add(new_chat)
            session.commit()
            return True  # Successfully registered
        except Exception as e:
            session.rollback()
            print(f"Error registering chat: {e}")
            return False
        finally:
            session.close()
