from typing import List

from common.enums import FeatureFlags
from config import get_db_session
from helper import force_log
from models import ShiftPermission
from services.group_package_service import GroupPackageService


class ShiftPermissionService:
    """Service for managing shift close permissions"""
    
    def __init__(self):
        self.group_package_service = GroupPackageService()
    
    async def add_allowed_user(self, chat_id: int, username: str) -> bool:
        """Add a user to the allowed list for closing shifts"""
        try:
            # Remove @ from username if present
            username = username.lstrip('@').lower()
            
            with get_db_session() as db:
                # Check if permission already exists
                existing = (
                    db.query(ShiftPermission)
                    .filter(
                        ShiftPermission.chat_id == chat_id,
                        ShiftPermission.username == username
                    )
                    .first()
                )
                
                if existing:
                    force_log(f"User @{username} already has close shift permission for chat {chat_id}")
                    return False
                
                # Add new permission
                permission = ShiftPermission(
                    chat_id=chat_id,
                    username=username
                )
                db.add(permission)
                db.commit()
                
                # Check if this is the first user - if so, enable the feature flag
                count = (
                    db.query(ShiftPermission)
                    .filter(ShiftPermission.chat_id == chat_id)
                    .count()
                )
                
                if count == 1:
                    # This is the first user, enable the feature flag
                    await self.group_package_service.set_feature_flag(
                        chat_id, FeatureFlags.SHIFT_PERMISSIONS.value, True
                    )
                    force_log(f"Enabled SHIFT_PERMISSIONS feature for chat {chat_id} (first user added)")
                
                force_log(f"Added close shift permission for user @{username} in chat {chat_id}")
                return True
                
        except Exception as e:
            force_log(f"Error adding shift permission for user @{username} in chat {chat_id}: {e}", "ERROR")
            return False
    
    async def remove_allowed_user(self, chat_id: int, username: str) -> bool:
        """Remove a user from the allowed list"""
        try:
            # Remove @ from username if present
            username = username.lstrip('@').lower()
            
            with get_db_session() as db:
                permission = (
                    db.query(ShiftPermission)
                    .filter(
                        ShiftPermission.chat_id == chat_id,
                        ShiftPermission.username == username
                    )
                    .first()
                )
                
                if not permission:
                    force_log(f"User @{username} does not have close shift permission for chat {chat_id}")
                    return False
                
                db.delete(permission)
                db.commit()
                
                # Check if there are no more users - if so, disable the feature flag
                count = (
                    db.query(ShiftPermission)
                    .filter(ShiftPermission.chat_id == chat_id)
                    .count()
                )
                
                if count == 0:
                    # No more users, disable the feature flag
                    await self.group_package_service.set_feature_flag(
                        chat_id, FeatureFlags.SHIFT_PERMISSIONS.value, False
                    )
                    force_log(f"Disabled SHIFT_PERMISSIONS feature for chat {chat_id} (no users remaining)")
                
                force_log(f"Removed close shift permission for user @{username} in chat {chat_id}")
                return True
                
        except Exception as e:
            force_log(f"Error removing shift permission for user @{username} in chat {chat_id}: {e}", "ERROR")
            return False
    
    async def is_user_allowed(self, chat_id: int, username: str) -> bool:
        """Check if a user is allowed to close shifts"""
        try:
            if not username:
                return False
                
            # Remove @ from username if present
            username = username.lstrip('@').lower()
            
            with get_db_session() as db:
                permission = (
                    db.query(ShiftPermission)
                    .filter(
                        ShiftPermission.chat_id == chat_id,
                        ShiftPermission.username == username
                    )
                    .first()
                )
                
                return permission is not None
                
        except Exception as e:
            force_log(f"Error checking shift permission for user @{username} in chat {chat_id}: {e}", "ERROR")
            return False
    
    async def get_allowed_users(self, chat_id: int) -> List[str]:
        """Get list of users allowed to close shifts"""
        try:
            with get_db_session() as db:
                permissions = (
                    db.query(ShiftPermission)
                    .filter(ShiftPermission.chat_id == chat_id)
                    .all()
                )
                
                return [f"@{permission.username}" for permission in permissions]
                
        except Exception as e:
            force_log(f"Error getting allowed users for chat {chat_id}: {e}", "ERROR")
            return []
    
    async def clear_all_permissions(self, chat_id: int) -> int:
        """Clear all permissions for a chat"""
        try:
            with get_db_session() as db:
                count = (
                    db.query(ShiftPermission)
                    .filter(ShiftPermission.chat_id == chat_id)
                    .count()
                )
                
                db.query(ShiftPermission).filter(
                    ShiftPermission.chat_id == chat_id
                ).delete()
                db.commit()
                
                # Disable the feature flag since all users are removed
                if count > 0:
                    await self.group_package_service.set_feature_flag(
                        chat_id, FeatureFlags.SHIFT_PERMISSIONS.value, False
                    )
                    force_log(f"Disabled SHIFT_PERMISSIONS feature for chat {chat_id} (all users cleared)")
                
                force_log(f"Cleared {count} shift permissions for chat {chat_id}")
                return count
                
        except Exception as e:
            force_log(f"Error clearing permissions for chat {chat_id}: {e}", "ERROR")
            return 0