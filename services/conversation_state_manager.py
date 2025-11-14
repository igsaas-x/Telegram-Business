from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from helper.logger_utils import force_log


class ConversationState(Enum):
    """Conversation states for interactive commands"""

    IDLE = "idle"
    WAITING_FOR_ACCOUNT_NUMBER = "waiting_for_account_number"
    WAITING_FOR_NAME = "waiting_for_name"
    WAITING_FOR_NICKNAME = "waiting_for_nickname"
    WAITING_FOR_NEW_NAME = "waiting_for_new_name"
    WAITING_FOR_CATEGORY_SELECTION = "waiting_for_category_selection"
    WAITING_FOR_DELETE_CONFIRMATION = "waiting_for_delete_confirmation"


class ConversationData:
    """Data container for conversation context"""

    def __init__(self, state: ConversationState, command: str):
        self.state = state
        self.command = command  # e.g., "sender_add", "sender_delete", "sender_update"
        self.data: dict[str, Any] = {}
        self.created_at = datetime.now()
        self.last_updated = datetime.now()

    def update(self, **kwargs):
        """Update conversation data"""
        self.data.update(kwargs)
        self.last_updated = datetime.now()

    def is_expired(self, timeout_minutes: int = 5) -> bool:
        """Check if conversation has timed out"""
        return datetime.now() > self.last_updated + timedelta(minutes=timeout_minutes)


class ConversationStateManager:
    """
    Manages conversation states for interactive bot commands.

    This is an in-memory state manager that tracks multi-step conversations
    for each user in each chat.
    """

    def __init__(self):
        # Key: (chat_id, user_id) -> ConversationData
        self._conversations: dict[tuple[int, int], ConversationData] = {}

    def start_conversation(
        self, chat_id: int, user_id: int, command: str, initial_state: ConversationState
    ) -> None:
        """
        Start a new conversation.

        Args:
            chat_id: The chat ID
            user_id: The user ID
            command: The command being executed (e.g., "sender_add")
            initial_state: The initial conversation state
        """
        key = (chat_id, user_id)

        # Clean up expired conversations
        self._cleanup_expired()

        # Create new conversation
        self._conversations[key] = ConversationData(initial_state, command)

        force_log(
            f"Started conversation for user {user_id} in chat {chat_id}: {command} -> {initial_state.value}",
            "ConversationStateManager",
        )

    def get_state(self, chat_id: int, user_id: int) -> ConversationState | None:
        """
        Get the current conversation state for a user.

        Args:
            chat_id: The chat ID
            user_id: The user ID

        Returns:
            Current ConversationState or None if no active conversation
        """
        key = (chat_id, user_id)
        conversation = self._conversations.get(key)

        if not conversation:
            return None

        # Check if expired
        if conversation.is_expired():
            self.end_conversation(chat_id, user_id)
            return None

        return conversation.state

    def update_state(
        self, chat_id: int, user_id: int, new_state: ConversationState, **data
    ) -> bool:
        """
        Update conversation state and data.

        Args:
            chat_id: The chat ID
            user_id: The user ID
            new_state: The new conversation state
            **data: Additional data to store in conversation context

        Returns:
            True if updated successfully, False if no active conversation
        """
        key = (chat_id, user_id)
        conversation = self._conversations.get(key)

        if not conversation:
            force_log(
                f"Cannot update state: No active conversation for user {user_id} in chat {chat_id}",
                "ConversationStateManager",
                "WARN",
            )
            return False

        # Check if expired
        if conversation.is_expired():
            self.end_conversation(chat_id, user_id)
            force_log(
                f"Cannot update state: Conversation expired for user {user_id} in chat {chat_id}",
                "ConversationStateManager",
                "WARN",
            )
            return False

        # Update state and data
        conversation.state = new_state
        conversation.update(**data)

        force_log(
            f"Updated conversation for user {user_id} in chat {chat_id}: {new_state.value}",
            "ConversationStateManager",
        )

        return True

    def get_data(self, chat_id: int, user_id: int) -> dict[str, Any] | None:
        """
        Get conversation data for a user.

        Args:
            chat_id: The chat ID
            user_id: The user ID

        Returns:
            Conversation data dict or None if no active conversation
        """
        key = (chat_id, user_id)
        conversation = self._conversations.get(key)

        if not conversation:
            return None

        # Check if expired
        if conversation.is_expired():
            self.end_conversation(chat_id, user_id)
            return None

        return conversation.data.copy()

    def end_conversation(self, chat_id: int, user_id: int) -> None:
        """
        End a conversation and clean up state.

        Args:
            chat_id: The chat ID
            user_id: The user ID
        """
        key = (chat_id, user_id)

        if key in self._conversations:
            command = self._conversations[key].command
            del self._conversations[key]

            force_log(
                f"Ended conversation for user {user_id} in chat {chat_id}: {command}",
                "ConversationStateManager",
            )

    def cancel_conversation(self, chat_id: int, user_id: int) -> bool:
        """
        Cancel an active conversation.

        Args:
            chat_id: The chat ID
            user_id: The user ID

        Returns:
            True if a conversation was cancelled, False if no active conversation
        """
        key = (chat_id, user_id)

        if key in self._conversations:
            self.end_conversation(chat_id, user_id)
            return True

        return False

    def is_in_conversation(self, chat_id: int, user_id: int) -> bool:
        """
        Check if a user is in an active conversation.

        Args:
            chat_id: The chat ID
            user_id: The user ID

        Returns:
            True if user has an active conversation, False otherwise
        """
        state = self.get_state(chat_id, user_id)
        return state is not None and state != ConversationState.IDLE

    def get_command(self, chat_id: int, user_id: int) -> str | None:
        """
        Get the command associated with current conversation.

        Args:
            chat_id: The chat ID
            user_id: The user ID

        Returns:
            Command name or None if no active conversation
        """
        key = (chat_id, user_id)
        conversation = self._conversations.get(key)

        if not conversation:
            return None

        # Check if expired
        if conversation.is_expired():
            self.end_conversation(chat_id, user_id)
            return None

        return conversation.command

    def _cleanup_expired(self) -> None:
        """Clean up expired conversations"""
        expired_keys = []

        for key, conversation in self._conversations.items():
            if conversation.is_expired():
                expired_keys.append(key)

        for key in expired_keys:
            chat_id, user_id = key
            force_log(
                f"Cleaning up expired conversation for user {user_id} in chat {chat_id}",
                "ConversationStateManager",
            )
            del self._conversations[key]

    def get_active_conversations_count(self) -> int:
        """Get count of active conversations (for debugging/monitoring)"""
        self._cleanup_expired()
        return len(self._conversations)
