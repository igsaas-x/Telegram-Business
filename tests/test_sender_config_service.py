import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path to import modules directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.sender_config_service import SenderConfigService
from models.sender_config_model import SenderConfig


class TestSenderConfigService(unittest.IsolatedAsyncioTestCase):
    """Unit tests for SenderConfigService"""

    def setUp(self):
        """Set up test fixtures"""
        self.service = SenderConfigService()
        self.test_chat_id = 123456789
        self.test_account_number = "708"
        self.test_sender_name = "John Doe"

    @patch("services.sender_config_service.get_db_session")
    async def test_add_sender_success(self, mock_get_db_session):
        """Test successfully adding a new sender"""
        # Mock session
        mock_session = MagicMock()
        mock_get_db_session.return_value.__enter__.return_value = mock_session

        # Execute
        success, message = await self.service.add_sender(
            self.test_chat_id, self.test_account_number, self.test_sender_name
        )

        # Assert
        self.assertTrue(success)
        self.assertIn("✅ Sender added", message)
        self.assertIn("708", message)
        self.assertIn("John Doe", message)
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch("services.sender_config_service.get_db_session")
    async def test_add_sender_invalid_account_number_length(self, mock_get_db_session):
        """Test adding sender with invalid account number length"""
        # Mock session
        mock_session = MagicMock()
        mock_get_db_session.return_value.__enter__.return_value = mock_session

        # Execute with 4 digits
        success, message = await self.service.add_sender(
            self.test_chat_id, "1234", self.test_sender_name
        )

        # Assert
        self.assertFalse(success)
        self.assertIn("exactly 3 digits", message)
        mock_session.add.assert_not_called()

    @patch("services.sender_config_service.get_db_session")
    async def test_add_sender_invalid_account_number_non_digit(
        self, mock_get_db_session
    ):
        """Test adding sender with non-digit account number"""
        # Mock session
        mock_session = MagicMock()
        mock_get_db_session.return_value.__enter__.return_value = mock_session

        # Execute with non-digits
        success, message = await self.service.add_sender(
            self.test_chat_id, "abc", self.test_sender_name
        )

        # Assert
        self.assertFalse(success)
        self.assertIn("exactly 3 digits", message)
        mock_session.add.assert_not_called()

    @patch("services.sender_config_service.get_db_session")
    async def test_add_sender_duplicate(self, mock_get_db_session):
        """Test adding duplicate sender (IntegrityError)"""
        from sqlalchemy.exc import IntegrityError

        # Mock session to raise IntegrityError
        mock_session = MagicMock()
        mock_session.commit.side_effect = IntegrityError("", "", "")
        mock_get_db_session.return_value.__enter__.return_value = mock_session

        # Execute
        success, message = await self.service.add_sender(
            self.test_chat_id, self.test_account_number, self.test_sender_name
        )

        # Assert
        self.assertFalse(success)
        self.assertIn("already exists", message)
        mock_session.rollback.assert_called_once()

    @patch("services.sender_config_service.get_db_session")
    async def test_delete_sender_success(self, mock_get_db_session):
        """Test successfully deleting a sender"""
        # Create mock sender
        mock_sender = SenderConfig(
            id=1,
            chat_id=self.test_chat_id,
            sender_account_number=self.test_account_number,
            sender_name=self.test_sender_name,
            is_active=True,
        )

        # Mock session and query
        mock_session = MagicMock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            mock_sender
        )
        mock_get_db_session.return_value.__enter__.return_value = mock_session

        # Execute
        success, message = await self.service.delete_sender(
            self.test_chat_id, self.test_account_number
        )

        # Assert
        self.assertTrue(success)
        self.assertIn("✅ Sender deleted", message)
        self.assertIn("708", message)
        mock_session.delete.assert_called_once_with(mock_sender)
        mock_session.commit.assert_called_once()

    @patch("services.sender_config_service.get_db_session")
    async def test_delete_sender_not_found(self, mock_get_db_session):
        """Test deleting non-existent sender"""
        # Mock session to return None
        mock_session = MagicMock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_get_db_session.return_value.__enter__.return_value = mock_session

        # Execute
        success, message = await self.service.delete_sender(
            self.test_chat_id, self.test_account_number
        )

        # Assert
        self.assertFalse(success)
        self.assertIn("not found", message)
        mock_session.delete.assert_not_called()

    @patch("services.sender_config_service.get_db_session")
    async def test_update_sender_success(self, mock_get_db_session):
        """Test successfully updating a sender"""
        # Mock session and query
        mock_session = MagicMock()
        mock_session.query.return_value.filter_by.return_value.update.return_value = 1
        mock_get_db_session.return_value.__enter__.return_value = mock_session

        # Execute
        new_name = "Jane Doe"
        success, message = await self.service.update_sender(
            self.test_chat_id, self.test_account_number, new_name
        )

        # Assert
        self.assertTrue(success)
        self.assertIn("✅ Sender updated", message)
        self.assertIn("708", message)
        self.assertIn("Jane Doe", message)
        mock_session.commit.assert_called_once()

    @patch("services.sender_config_service.get_db_session")
    async def test_update_sender_not_found(self, mock_get_db_session):
        """Test updating non-existent sender"""
        # Mock session to return 0 rows updated
        mock_session = MagicMock()
        mock_session.query.return_value.filter_by.return_value.update.return_value = 0
        mock_get_db_session.return_value.__enter__.return_value = mock_session

        # Execute
        success, message = await self.service.update_sender(
            self.test_chat_id, self.test_account_number, "New Name"
        )

        # Assert
        self.assertFalse(success)
        self.assertIn("not found", message)

    @patch("services.sender_config_service.get_db_session")
    async def test_get_senders_active_only(self, mock_get_db_session):
        """Test getting only active senders"""
        # Create mock senders
        mock_senders = [
            SenderConfig(
                id=1,
                chat_id=self.test_chat_id,
                sender_account_number="708",
                sender_name="John",
                is_active=True,
            ),
            SenderConfig(
                id=2,
                chat_id=self.test_chat_id,
                sender_account_number="332",
                sender_name="Jane",
                is_active=True,
            ),
        ]

        # Mock session and query
        mock_session = MagicMock()
        mock_query = mock_session.query.return_value
        mock_query.filter_by.return_value.filter_by.return_value.order_by.return_value.all.return_value = (
            mock_senders
        )
        mock_get_db_session.return_value.__enter__.return_value = mock_session

        # Execute
        senders = await self.service.get_senders(self.test_chat_id, active_only=True)

        # Assert
        self.assertEqual(len(senders), 2)
        self.assertEqual(senders[0].sender_account_number, "708")
        self.assertEqual(senders[1].sender_account_number, "332")

    @patch("services.sender_config_service.get_db_session")
    async def test_get_sender_by_account_number_found(self, mock_get_db_session):
        """Test getting sender by account number when found"""
        # Create mock sender
        mock_sender = SenderConfig(
            id=1,
            chat_id=self.test_chat_id,
            sender_account_number=self.test_account_number,
            sender_name=self.test_sender_name,
            is_active=True,
        )

        # Mock session and query
        mock_session = MagicMock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            mock_sender
        )
        mock_get_db_session.return_value.__enter__.return_value = mock_session

        # Execute
        sender = await self.service.get_sender_by_account_number(
            self.test_chat_id, self.test_account_number
        )

        # Assert
        self.assertIsNotNone(sender)
        self.assertEqual(sender.sender_account_number, "708")
        self.assertEqual(sender.sender_name, "John Doe")

    @patch("services.sender_config_service.get_db_session")
    async def test_get_sender_by_account_number_not_found(self, mock_get_db_session):
        """Test getting sender by account number when not found"""
        # Mock session to return None
        mock_session = MagicMock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_get_db_session.return_value.__enter__.return_value = mock_session

        # Execute
        sender = await self.service.get_sender_by_account_number(
            self.test_chat_id, "999"
        )

        # Assert
        self.assertIsNone(sender)

    @patch("services.sender_config_service.get_db_session")
    async def test_get_sender_account_numbers(self, mock_get_db_session):
        """Test getting all sender account numbers"""
        # Mock query result
        mock_result = [("708",), ("332",), ("445",)]

        # Mock session and query
        mock_session = MagicMock()
        mock_session.query.return_value.filter_by.return_value.all.return_value = (
            mock_result
        )
        mock_get_db_session.return_value.__enter__.return_value = mock_session

        # Execute
        account_numbers = await self.service.get_sender_account_numbers(
            self.test_chat_id
        )

        # Assert
        self.assertEqual(len(account_numbers), 3)
        self.assertEqual(account_numbers, ["708", "332", "445"])


if __name__ == "__main__":
    unittest.main()
