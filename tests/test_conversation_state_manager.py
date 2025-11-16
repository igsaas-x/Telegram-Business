import unittest
from datetime import datetime, timedelta

from services.conversation_state_manager import (
    ConversationState,
    ConversationStateManager,
    ConversationData,
)


class TestConversationData(unittest.TestCase):
    """Unit tests for ConversationData"""

    def test_init(self):
        """Test ConversationData initialization"""
        data = ConversationData(ConversationState.WAITING_FOR_ACCOUNT_NUMBER, "sender_add")

        self.assertEqual(data.state, ConversationState.WAITING_FOR_ACCOUNT_NUMBER)
        self.assertEqual(data.command, "sender_add")
        self.assertEqual(data.data, {})
        self.assertIsInstance(data.created_at, datetime)
        self.assertIsInstance(data.last_updated, datetime)

    def test_update(self):
        """Test updating conversation data"""
        data = ConversationData(ConversationState.WAITING_FOR_ACCOUNT_NUMBER, "sender_add")
        initial_update_time = data.last_updated

        # Wait a tiny bit
        import time
        time.sleep(0.01)

        # Update with data
        data.update(account_number="708", temp_value="test")

        self.assertEqual(data.data["account_number"], "708")
        self.assertEqual(data.data["temp_value"], "test")
        self.assertGreater(data.last_updated, initial_update_time)

    def test_is_expired_not_expired(self):
        """Test is_expired returns False for recent conversations"""
        data = ConversationData(ConversationState.WAITING_FOR_ACCOUNT_NUMBER, "sender_add")

        self.assertFalse(data.is_expired(timeout_minutes=5))

    def test_is_expired_expired(self):
        """Test is_expired returns True for old conversations"""
        data = ConversationData(ConversationState.WAITING_FOR_ACCOUNT_NUMBER, "sender_add")

        # Manually set last_updated to 10 minutes ago
        data.last_updated = datetime.now() - timedelta(minutes=10)

        self.assertTrue(data.is_expired(timeout_minutes=5))


class TestConversationStateManager(unittest.TestCase):
    """Unit tests for ConversationStateManager"""

    def setUp(self):
        """Set up test fixtures"""
        self.manager = ConversationStateManager()
        self.test_chat_id = 123456789
        self.test_user_id = 987654321

    def test_start_conversation(self):
        """Test starting a new conversation"""
        self.manager.start_conversation(
            self.test_chat_id,
            self.test_user_id,
            "sender_add",
            ConversationState.WAITING_FOR_ACCOUNT_NUMBER,
        )

        state = self.manager.get_state(self.test_chat_id, self.test_user_id)
        self.assertEqual(state, ConversationState.WAITING_FOR_ACCOUNT_NUMBER)

    def test_get_state_no_conversation(self):
        """Test getting state when no conversation exists"""
        state = self.manager.get_state(self.test_chat_id, self.test_user_id)
        self.assertIsNone(state)

    def test_update_state_success(self):
        """Test successfully updating conversation state"""
        # Start conversation
        self.manager.start_conversation(
            self.test_chat_id,
            self.test_user_id,
            "sender_add",
            ConversationState.WAITING_FOR_ACCOUNT_NUMBER,
        )

        # Update state
        success = self.manager.update_state(
            self.test_chat_id,
            self.test_user_id,
            ConversationState.WAITING_FOR_NAME,
            account_number="708",
        )

        # Assert
        self.assertTrue(success)
        state = self.manager.get_state(self.test_chat_id, self.test_user_id)
        self.assertEqual(state, ConversationState.WAITING_FOR_NAME)

        data = self.manager.get_data(self.test_chat_id, self.test_user_id)
        self.assertEqual(data["account_number"], "708")

    def test_update_state_no_conversation(self):
        """Test updating state when no conversation exists"""
        success = self.manager.update_state(
            self.test_chat_id,
            self.test_user_id,
            ConversationState.WAITING_FOR_NAME,
        )

        self.assertFalse(success)

    def test_get_data_with_conversation(self):
        """Test getting data when conversation exists"""
        # Start and update conversation
        self.manager.start_conversation(
            self.test_chat_id,
            self.test_user_id,
            "sender_add",
            ConversationState.WAITING_FOR_ACCOUNT_NUMBER,
        )
        self.manager.update_state(
            self.test_chat_id,
            self.test_user_id,
            ConversationState.WAITING_FOR_NAME,
            account_number="708",
            test_field="value",
        )

        # Get data
        data = self.manager.get_data(self.test_chat_id, self.test_user_id)

        self.assertIsNotNone(data)
        self.assertEqual(data["account_number"], "708")
        self.assertEqual(data["test_field"], "value")

    def test_get_data_no_conversation(self):
        """Test getting data when no conversation exists"""
        data = self.manager.get_data(self.test_chat_id, self.test_user_id)
        self.assertIsNone(data)

    def test_end_conversation(self):
        """Test ending a conversation"""
        # Start conversation
        self.manager.start_conversation(
            self.test_chat_id,
            self.test_user_id,
            "sender_add",
            ConversationState.WAITING_FOR_ACCOUNT_NUMBER,
        )

        # Verify it exists
        self.assertTrue(
            self.manager.is_in_conversation(self.test_chat_id, self.test_user_id)
        )

        # End conversation
        self.manager.end_conversation(self.test_chat_id, self.test_user_id)

        # Verify it's gone
        state = self.manager.get_state(self.test_chat_id, self.test_user_id)
        self.assertIsNone(state)

    def test_cancel_conversation_exists(self):
        """Test cancelling an existing conversation"""
        # Start conversation
        self.manager.start_conversation(
            self.test_chat_id,
            self.test_user_id,
            "sender_add",
            ConversationState.WAITING_FOR_ACCOUNT_NUMBER,
        )

        # Cancel
        result = self.manager.cancel_conversation(self.test_chat_id, self.test_user_id)

        # Assert
        self.assertTrue(result)
        self.assertFalse(
            self.manager.is_in_conversation(self.test_chat_id, self.test_user_id)
        )

    def test_cancel_conversation_not_exists(self):
        """Test cancelling when no conversation exists"""
        result = self.manager.cancel_conversation(self.test_chat_id, self.test_user_id)
        self.assertFalse(result)

    def test_is_in_conversation_true(self):
        """Test is_in_conversation returns True for active conversation"""
        self.manager.start_conversation(
            self.test_chat_id,
            self.test_user_id,
            "sender_add",
            ConversationState.WAITING_FOR_ACCOUNT_NUMBER,
        )

        self.assertTrue(
            self.manager.is_in_conversation(self.test_chat_id, self.test_user_id)
        )

    def test_is_in_conversation_false(self):
        """Test is_in_conversation returns False when no conversation"""
        self.assertFalse(
            self.manager.is_in_conversation(self.test_chat_id, self.test_user_id)
        )

    def test_get_command(self):
        """Test getting command associated with conversation"""
        self.manager.start_conversation(
            self.test_chat_id,
            self.test_user_id,
            "sender_add",
            ConversationState.WAITING_FOR_ACCOUNT_NUMBER,
        )

        command = self.manager.get_command(self.test_chat_id, self.test_user_id)
        self.assertEqual(command, "sender_add")

    def test_get_command_no_conversation(self):
        """Test getting command when no conversation exists"""
        command = self.manager.get_command(self.test_chat_id, self.test_user_id)
        self.assertIsNone(command)

    def test_expired_conversation_cleaned_on_get_state(self):
        """Test that expired conversations are cleaned up when getting state"""
        # Start conversation
        self.manager.start_conversation(
            self.test_chat_id,
            self.test_user_id,
            "sender_add",
            ConversationState.WAITING_FOR_ACCOUNT_NUMBER,
        )

        # Manually expire the conversation
        key = (self.test_chat_id, self.test_user_id)
        self.manager._conversations[key].last_updated = datetime.now() - timedelta(
            minutes=10
        )

        # Try to get state (should clean up and return None)
        state = self.manager.get_state(self.test_chat_id, self.test_user_id)

        self.assertIsNone(state)
        self.assertNotIn(key, self.manager._conversations)

    def test_multiple_users_separate_conversations(self):
        """Test that multiple users can have separate conversations"""
        user_1 = 111
        user_2 = 222

        # Start conversations for two different users
        self.manager.start_conversation(
            self.test_chat_id, user_1, "sender_add", ConversationState.WAITING_FOR_ACCOUNT_NUMBER
        )
        self.manager.start_conversation(
            self.test_chat_id, user_2, "sender_delete", ConversationState.WAITING_FOR_ACCOUNT_NUMBER
        )

        # Verify both conversations exist independently
        command_1 = self.manager.get_command(self.test_chat_id, user_1)
        command_2 = self.manager.get_command(self.test_chat_id, user_2)

        self.assertEqual(command_1, "sender_add")
        self.assertEqual(command_2, "sender_delete")

        # End one conversation
        self.manager.end_conversation(self.test_chat_id, user_1)

        # Verify only the correct one was ended
        self.assertFalse(self.manager.is_in_conversation(self.test_chat_id, user_1))
        self.assertTrue(self.manager.is_in_conversation(self.test_chat_id, user_2))

    def test_get_active_conversations_count(self):
        """Test getting count of active conversations"""
        # Initially should be 0
        self.assertEqual(self.manager.get_active_conversations_count(), 0)

        # Add some conversations
        self.manager.start_conversation(
            self.test_chat_id, 111, "sender_add", ConversationState.WAITING_FOR_ACCOUNT_NUMBER
        )
        self.manager.start_conversation(
            self.test_chat_id, 222, "sender_delete", ConversationState.WAITING_FOR_ACCOUNT_NUMBER
        )

        self.assertEqual(self.manager.get_active_conversations_count(), 2)

        # End one
        self.manager.end_conversation(self.test_chat_id, 111)

        self.assertEqual(self.manager.get_active_conversations_count(), 1)


if __name__ == "__main__":
    unittest.main()
