from sqlalchemy.exc import IntegrityError

from config import get_db_session
from helper.logger_utils import force_log
from models.sender_config_model import SenderConfig


class SenderConfigService:
    """Service for managing sender configurations"""

    @staticmethod
    async def add_sender(
        chat_id: int, sender_account_number: str, sender_name: str | None = None
    ) -> tuple[bool, str]:
        """
        Add a new sender configuration.

        Args:
            chat_id: The chat ID
            sender_account_number: Last 3 digits of account number
            sender_name: Optional sender name

        Returns:
            Tuple of (success: bool, message: str)
        """
        with get_db_session() as session:
            try:
                # Validate account number is exactly 3 digits
                if not sender_account_number.isdigit() or len(sender_account_number) != 3:
                    return False, "Account number must be exactly 3 digits"

                new_sender = SenderConfig(
                    chat_id=chat_id,
                    sender_account_number=sender_account_number,
                    sender_name=sender_name,
                    is_active=True,
                )
                session.add(new_sender)
                session.commit()

                sender_display = f"{sender_account_number}"
                if sender_name:
                    sender_display += f" ({sender_name})"

                return True, f"✅ Sender added: {sender_display}"

            except IntegrityError:
                session.rollback()
                sender_display = f"{sender_account_number}"
                if sender_name:
                    sender_display += f" ({sender_name})"
                return False, f"❌ Sender {sender_display} already exists for this chat"

            except Exception as e:
                session.rollback()
                force_log(f"Error adding sender: {e}", "SenderConfigService", "ERROR")
                return False, f"Error adding sender: {str(e)}"

            finally:
                session.close()

    @staticmethod
    async def delete_sender(chat_id: int, sender_account_number: str) -> tuple[bool, str]:
        """
        Delete a sender configuration.

        Args:
            chat_id: The chat ID
            sender_account_number: Last 3 digits of account number

        Returns:
            Tuple of (success: bool, message: str)
        """
        with get_db_session() as session:
            try:
                sender = (
                    session.query(SenderConfig)
                    .filter_by(
                        chat_id=chat_id, sender_account_number=sender_account_number
                    )
                    .first()
                )

                if not sender:
                    return False, f"❌ Sender {sender_account_number} not found"

                sender_display = f"{sender_account_number}"
                if sender.sender_name:
                    sender_display += f" ({sender.sender_name})"

                session.delete(sender)
                session.commit()

                return True, f"✅ Sender deleted: {sender_display}"

            except Exception as e:
                session.rollback()
                force_log(
                    f"Error deleting sender: {e}", "SenderConfigService", "ERROR"
                )
                return False, f"Error deleting sender: {str(e)}"

            finally:
                session.close()

    @staticmethod
    async def update_sender(
        chat_id: int, sender_account_number: str, sender_name: str | None = None
    ) -> tuple[bool, str]:
        """
        Update a sender's name.

        Args:
            chat_id: The chat ID
            sender_account_number: Last 3 digits of account number
            sender_name: New sender name

        Returns:
            Tuple of (success: bool, message: str)
        """
        with get_db_session() as session:
            try:
                result = (
                    session.query(SenderConfig)
                    .filter_by(
                        chat_id=chat_id, sender_account_number=sender_account_number
                    )
                    .update({"sender_name": sender_name})
                )

                if result == 0:
                    return False, f"❌ Sender {sender_account_number} not found"

                session.commit()

                sender_display = f"{sender_account_number}"
                if sender_name:
                    sender_display += f" ({sender_name})"

                return True, f"✅ Sender updated: {sender_display}"

            except Exception as e:
                session.rollback()
                force_log(
                    f"Error updating sender: {e}", "SenderConfigService", "ERROR"
                )
                return False, f"Error updating sender: {str(e)}"

            finally:
                session.close()

    @staticmethod
    async def get_senders(chat_id: int, active_only: bool = True) -> list[SenderConfig]:
        """
        Get all sender configurations for a chat.

        Args:
            chat_id: The chat ID
            active_only: If True, only return active senders

        Returns:
            List of SenderConfig objects
        """
        with get_db_session() as session:
            try:
                query = session.query(SenderConfig).filter_by(chat_id=chat_id)

                if active_only:
                    query = query.filter_by(is_active=True)

                senders = query.order_by(SenderConfig.sender_account_number).all()

                # Detach objects from session to prevent lazy loading errors
                session.expunge_all()

                return senders

            except Exception as e:
                force_log(
                    f"Error fetching senders: {e}", "SenderConfigService", "ERROR"
                )
                return []

            finally:
                session.close()

    @staticmethod
    async def get_sender_by_account_number(
        chat_id: int, sender_account_number: str
    ) -> SenderConfig | None:
        """
        Get a specific sender configuration.

        Args:
            chat_id: The chat ID
            sender_account_number: Last 3 digits of account number

        Returns:
            SenderConfig object or None if not found
        """
        with get_db_session() as session:
            try:
                sender = (
                    session.query(SenderConfig)
                    .filter_by(
                        chat_id=chat_id,
                        sender_account_number=sender_account_number,
                        is_active=True,
                    )
                    .first()
                )

                # Detach object from session to prevent lazy loading errors
                if sender:
                    session.expunge(sender)

                return sender

            except Exception as e:
                force_log(
                    f"Error fetching sender: {e}", "SenderConfigService", "ERROR"
                )
                return None

            finally:
                session.close()

    @staticmethod
    async def get_sender_account_numbers(chat_id: int) -> list[str]:
        """
        Get all sender account numbers for a chat.

        Args:
            chat_id: The chat ID

        Returns:
            List of account numbers (3-digit strings)
        """
        with get_db_session() as session:
            try:
                result = (
                    session.query(SenderConfig.sender_account_number)
                    .filter_by(chat_id=chat_id, is_active=True)
                    .all()
                )

                return [r[0] for r in result]

            except Exception as e:
                force_log(
                    f"Error fetching sender account numbers: {e}",
                    "SenderConfigService",
                    "ERROR",
                )
                return []

            finally:
                session.close()
