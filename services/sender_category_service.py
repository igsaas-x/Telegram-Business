from sqlalchemy.exc import IntegrityError

from config import get_db_session
from helper.logger_utils import force_log
from models.sender_category_model import SenderCategory
from models.sender_config_model import SenderConfig


class SenderCategoryService:
    """Service for managing sender categories"""

    @staticmethod
    async def create_category(
        chat_id: int, category_name: str, display_order: int = 0
    ) -> tuple[bool, str]:
        """
        Create a new sender category.

        Args:
            chat_id: The chat ID
            category_name: Name of the category
            display_order: Display order (default: 0)

        Returns:
            Tuple of (success: bool, message: str)
        """
        with get_db_session() as session:
            try:
                # Validate category name
                if not category_name or not category_name.strip():
                    return False, "❌ Category name cannot be empty"

                category_name = category_name.strip()

                if len(category_name) > 100:
                    return False, "❌ Category name must be 100 characters or less"

                new_category = SenderCategory(
                    chat_id=chat_id,
                    category_name=category_name,
                    display_order=display_order,
                    is_active=True,
                )
                session.add(new_category)
                session.commit()

                return True, f"✅ Category created: {category_name}"

            except IntegrityError:
                session.rollback()
                return False, f"❌ Category '{category_name}' already exists for this chat"

            except Exception as e:
                session.rollback()
                force_log(f"Error creating category: {e}", "SenderCategoryService", "ERROR")
                return False, f"Error creating category: {str(e)}"

            finally:
                session.close()

    @staticmethod
    async def delete_category(chat_id: int, category_name: str) -> tuple[bool, str]:
        """
        Delete a sender category.
        All senders in this category will have their category_id set to NULL.

        Args:
            chat_id: The chat ID
            category_name: Name of the category to delete

        Returns:
            Tuple of (success: bool, message: str)
        """
        with get_db_session() as session:
            try:
                category = (
                    session.query(SenderCategory)
                    .filter_by(chat_id=chat_id, category_name=category_name)
                    .first()
                )

                if not category:
                    return False, f"❌ Category '{category_name}' not found"

                # Count senders in this category
                sender_count = (
                    session.query(SenderConfig)
                    .filter_by(category_id=category.id)
                    .count()
                )

                session.delete(category)
                session.commit()

                message = f"✅ Category deleted: {category_name}"
                if sender_count > 0:
                    message += f" ({sender_count} sender{'s' if sender_count != 1 else ''} uncategorized)"

                return True, message

            except Exception as e:
                session.rollback()
                force_log(
                    f"Error deleting category: {e}", "SenderCategoryService", "ERROR"
                )
                return False, f"Error deleting category: {str(e)}"

            finally:
                session.close()

    @staticmethod
    async def update_category(
        chat_id: int,
        old_category_name: str,
        new_category_name: str | None = None,
        new_display_order: int | None = None,
    ) -> tuple[bool, str]:
        """
        Update a category's name and/or display order.

        Args:
            chat_id: The chat ID
            old_category_name: Current category name
            new_category_name: New category name (if changing)
            new_display_order: New display order (if changing)

        Returns:
            Tuple of (success: bool, message: str)
        """
        with get_db_session() as session:
            try:
                category = (
                    session.query(SenderCategory)
                    .filter_by(chat_id=chat_id, category_name=old_category_name)
                    .first()
                )

                if not category:
                    return False, f"❌ Category '{old_category_name}' not found"

                # Validate new category name if provided
                if new_category_name is not None:
                    new_category_name = new_category_name.strip()
                    if not new_category_name:
                        return False, "❌ Category name cannot be empty"
                    if len(new_category_name) > 100:
                        return False, "❌ Category name must be 100 characters or less"
                    category.category_name = new_category_name

                if new_display_order is not None:
                    category.display_order = new_display_order

                session.commit()

                display_name = new_category_name if new_category_name else old_category_name
                return True, f"✅ Category updated: {display_name}"

            except IntegrityError:
                session.rollback()
                return False, f"❌ Category '{new_category_name}' already exists for this chat"

            except Exception as e:
                session.rollback()
                force_log(
                    f"Error updating category: {e}", "SenderCategoryService", "ERROR"
                )
                return False, f"Error updating category: {str(e)}"

            finally:
                session.close()

    @staticmethod
    async def list_categories(
        chat_id: int, active_only: bool = True
    ) -> list[SenderCategory]:
        """
        Get all categories for a chat, ordered by display_order.

        Args:
            chat_id: The chat ID
            active_only: If True, only return active categories

        Returns:
            List of SenderCategory objects
        """
        with get_db_session() as session:
            try:
                query = session.query(SenderCategory).filter_by(chat_id=chat_id)

                if active_only:
                    query = query.filter_by(is_active=True)

                categories = query.order_by(SenderCategory.display_order).all()

                # Detach objects from session to prevent lazy loading errors
                session.expunge_all()

                return categories

            except Exception as e:
                force_log(
                    f"Error fetching categories: {e}",
                    "SenderCategoryService",
                    "ERROR",
                )
                return []

            finally:
                session.close()

    @staticmethod
    async def get_category_by_id(category_id: int) -> SenderCategory | None:
        """
        Get a specific category by ID.

        Args:
            category_id: The category ID

        Returns:
            SenderCategory object or None if not found
        """
        with get_db_session() as session:
            try:
                category = (
                    session.query(SenderCategory)
                    .filter_by(id=category_id, is_active=True)
                    .first()
                )

                # Detach object from session to prevent lazy loading errors
                if category:
                    session.expunge(category)

                return category

            except Exception as e:
                force_log(
                    f"Error fetching category: {e}", "SenderCategoryService", "ERROR"
                )
                return None

            finally:
                session.close()

    @staticmethod
    async def get_category_by_name(
        chat_id: int, category_name: str
    ) -> SenderCategory | None:
        """
        Get a specific category by name.

        Args:
            chat_id: The chat ID
            category_name: The category name

        Returns:
            SenderCategory object or None if not found
        """
        with get_db_session() as session:
            try:
                category = (
                    session.query(SenderCategory)
                    .filter_by(
                        chat_id=chat_id,
                        category_name=category_name,
                        is_active=True,
                    )
                    .first()
                )

                # Detach object from session to prevent lazy loading errors
                if category:
                    session.expunge(category)

                return category

            except Exception as e:
                force_log(
                    f"Error fetching category: {e}", "SenderCategoryService", "ERROR"
                )
                return None

            finally:
                session.close()

    @staticmethod
    async def assign_sender_to_category(
        chat_id: int,
        sender_account_number: str,
        category_name: str | None,
    ) -> tuple[bool, str]:
        """
        Assign a sender to a category (or remove category assignment if None).

        Args:
            chat_id: The chat ID
            sender_account_number: Last 3 digits of sender account number
            category_name: Category name (None to remove category)

        Returns:
            Tuple of (success: bool, message: str)
        """
        with get_db_session() as session:
            try:
                # Find the sender
                sender = (
                    session.query(SenderConfig)
                    .filter_by(
                        chat_id=chat_id,
                        sender_account_number=sender_account_number,
                    )
                    .first()
                )

                if not sender:
                    return False, f"❌ Sender {sender_account_number} not found"

                # If category_name is None, remove category
                if category_name is None:
                    sender.category_id = None
                    session.commit()
                    return True, f"✅ Category removed from sender {sender.get_display_name()}"

                # Find the category
                category = (
                    session.query(SenderCategory)
                    .filter_by(chat_id=chat_id, category_name=category_name)
                    .first()
                )

                if not category:
                    return False, f"❌ Category '{category_name}' not found"

                sender.category_id = category.id
                session.commit()

                return True, f"✅ Sender {sender.get_display_name()} assigned to '{category_name}'"

            except Exception as e:
                session.rollback()
                force_log(
                    f"Error assigning sender to category: {e}",
                    "SenderCategoryService",
                    "ERROR",
                )
                return False, f"Error assigning sender: {str(e)}"

            finally:
                session.close()

    @staticmethod
    async def assign_multiple_senders(
        chat_id: int,
        sender_account_numbers: list[str],
        category_name: str,
    ) -> tuple[bool, str]:
        """
        Assign multiple senders to a category.

        Args:
            chat_id: The chat ID
            sender_account_numbers: List of sender account numbers
            category_name: Category name

        Returns:
            Tuple of (success: bool, message: str)
        """
        with get_db_session() as session:
            try:
                # Find the category
                category = (
                    session.query(SenderCategory)
                    .filter_by(chat_id=chat_id, category_name=category_name)
                    .first()
                )

                if not category:
                    return False, f"❌ Category '{category_name}' not found"

                # Find all senders
                senders = (
                    session.query(SenderConfig)
                    .filter(
                        SenderConfig.chat_id == chat_id,
                        SenderConfig.sender_account_number.in_(sender_account_numbers),
                    )
                    .all()
                )

                if not senders:
                    return False, "❌ No senders found"

                # Assign category to all senders
                count = 0
                for sender in senders:
                    sender.category_id = category.id
                    count += 1

                session.commit()

                return True, f"✅ {count} sender{'s' if count != 1 else ''} assigned to '{category_name}'"

            except Exception as e:
                session.rollback()
                force_log(
                    f"Error assigning multiple senders: {e}",
                    "SenderCategoryService",
                    "ERROR",
                )
                return False, f"Error assigning senders: {str(e)}"

            finally:
                session.close()

    @staticmethod
    async def get_senders_by_category(
        chat_id: int, category_name: str
    ) -> list[SenderConfig]:
        """
        Get all senders in a specific category.

        Args:
            chat_id: The chat ID
            category_name: The category name

        Returns:
            List of SenderConfig objects
        """
        with get_db_session() as session:
            try:
                # Find the category
                category = (
                    session.query(SenderCategory)
                    .filter_by(chat_id=chat_id, category_name=category_name)
                    .first()
                )

                if not category:
                    return []

                # Get all senders in this category
                senders = (
                    session.query(SenderConfig)
                    .filter_by(chat_id=chat_id, category_id=category.id, is_active=True)
                    .order_by(SenderConfig.sender_account_number)
                    .all()
                )

                # Detach objects from session to prevent lazy loading errors
                session.expunge_all()

                return senders

            except Exception as e:
                force_log(
                    f"Error fetching senders by category: {e}",
                    "SenderCategoryService",
                    "ERROR",
                )
                return []

            finally:
                session.close()

    @staticmethod
    async def update_sender_nickname(
        chat_id: int,
        sender_account_number: str,
        nickname: str | None,
    ) -> tuple[bool, str]:
        """
        Update a sender's nickname.

        Args:
            chat_id: The chat ID
            sender_account_number: Last 3 digits of sender account number
            nickname: New nickname (None to remove)

        Returns:
            Tuple of (success: bool, message: str)
        """
        with get_db_session() as session:
            try:
                sender = (
                    session.query(SenderConfig)
                    .filter_by(
                        chat_id=chat_id,
                        sender_account_number=sender_account_number,
                    )
                    .first()
                )

                if not sender:
                    return False, f"❌ Sender {sender_account_number} not found"

                # Validate nickname if provided
                if nickname is not None:
                    nickname = nickname.strip()
                    if len(nickname) > 100:
                        return False, "❌ Nickname must be 100 characters or less"
                    if not nickname:
                        nickname = None

                sender.nickname = nickname
                session.commit()

                if nickname:
                    return True, f"✅ Nickname set to '{nickname}' for sender {sender_account_number}"
                else:
                    return True, f"✅ Nickname removed from sender {sender_account_number}"

            except Exception as e:
                session.rollback()
                force_log(
                    f"Error updating sender nickname: {e}",
                    "SenderCategoryService",
                    "ERROR",
                )
                return False, f"Error updating nickname: {str(e)}"

            finally:
                session.close()
