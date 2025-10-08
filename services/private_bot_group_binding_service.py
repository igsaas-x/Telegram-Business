from typing import List

from config.database_config import get_db_session
from models.chat_model import Chat
from models.private_bot_group_binding_model import PrivateBotGroupBinding


class PrivateBotGroupBindingService:
    @staticmethod
    def bind_group(private_chat_id: int, group_id: int) -> PrivateBotGroupBinding:
        """Bind a private chat to a group"""
        with get_db_session() as session:
            # Check if binding already exists
            existing = session.query(PrivateBotGroupBinding).filter(
                PrivateBotGroupBinding.private_chat_id == private_chat_id,
                PrivateBotGroupBinding.bound_group_id == group_id
            ).first()
            
            if existing:
                return existing
            
            binding = PrivateBotGroupBinding(
                private_chat_id=private_chat_id,
                bound_group_id=group_id
            )
            session.add(binding)
            session.commit()
            session.refresh(binding)
            return binding

    @staticmethod
    def unbind_group(private_chat_id: int, group_id: int) -> bool:
        """Unbind a private chat from a group"""
        with get_db_session() as session:
            binding = session.query(PrivateBotGroupBinding).filter(
                PrivateBotGroupBinding.private_chat_id == private_chat_id,
                PrivateBotGroupBinding.bound_group_id == group_id
            ).first()
            
            if binding:
                session.delete(binding)
                session.commit()
                return True
            return False

    @staticmethod
    def get_bound_groups(private_chat_id: int) -> List[Chat]:
        """Get all groups bound to a private chat"""
        with get_db_session() as session:
            bindings = session.query(PrivateBotGroupBinding).filter(
                PrivateBotGroupBinding.private_chat_id == private_chat_id
            ).all()
            
            group_ids = [binding.bound_group_id for binding in bindings]
            if not group_ids:
                return []
            
            groups = session.query(Chat).filter(Chat.id.in_(group_ids)).all()
            return groups

    @staticmethod
    def get_private_chats_for_group(group_id: int) -> List[int]:
        """Get all private chats bound to a specific group"""
        with get_db_session() as session:
            bindings = session.query(PrivateBotGroupBinding).filter(
                PrivateBotGroupBinding.bound_group_id == group_id
            ).all()
            
            return [binding.private_chat_id for binding in bindings]

    @staticmethod
    def is_group_bound(private_chat_id: int, group_id: int) -> bool:
        """Check if a group is bound to a private chat"""
        with get_db_session() as session:
            binding = session.query(PrivateBotGroupBinding).filter(
                PrivateBotGroupBinding.private_chat_id == private_chat_id,
                PrivateBotGroupBinding.bound_group_id == group_id
            ).first()

            return binding is not None

    @staticmethod
    def get_all_with_daily_summary_time() -> List[tuple[int, str]]:
        """Get all private chat IDs with their configured daily summary times"""
        with get_db_session() as session:
            results = session.query(
                PrivateBotGroupBinding.private_chat_id,
                PrivateBotGroupBinding.daily_summary_time
            ).filter(
                PrivateBotGroupBinding.daily_summary_time.isnot(None)
            ).distinct().all()

            return [(r[0], r[1]) for r in results]