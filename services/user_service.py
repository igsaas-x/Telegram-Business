from models import User
from config import get_db_session


class UserService:
    async def get_user_by_identifier(self, identifier: str) -> User | None:
        with get_db_session() as db:
            user = db.query(User).filter(User.identifier == identifier).first()
            return user

    async def get_user_by_username(self, username: str) -> User | None:
        with get_db_session() as db:
            user = db.query(User).filter(User.username == username).first()
            return user

    async def create_user(self, sender) -> User:
        with get_db_session() as db:
            existing_user = (
                db.query(User)
                .filter(
                    (User.identifier == sender.id) | (User.username == sender.username)
                )
                .first()
            )

            # If user already exists, return it
            if existing_user:
                return existing_user

            # Create new user if not exists
            user = User(
                first_name=sender.first_name,
                last_name=sender.last_name,
                phone_number=sender.phone,
                identifier=sender.id,
                username=sender.username,
                is_active=False,
            )

            try:
                db.add(user)
                db.commit()
                db.refresh(user)
                return user
            except Exception as e:
                db.rollback()
                raise e
