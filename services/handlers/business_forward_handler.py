from __future__ import annotations

from typing import Iterable, Optional, Set

from telegram import Message, Update
from telegram.ext import ContextTypes

from helper.logger_utils import force_log
from services.income_message_processor import IncomeMessageProcessor


class BusinessForwardHandler:
    """Handle forwarded bank summaries that appear in business bot groups."""

    def __init__(
        self,
        *,
        allowed_forwarders: Iterable[str],
        allowed_bots: Iterable[str],
        message_processor: Optional[IncomeMessageProcessor] = None,
    ) -> None:
        self.allowed_forwarders: Set[str] = {name.lstrip("@") for name in allowed_forwarders}
        self.allowed_bots: Set[str] = {name.lstrip("@") for name in allowed_bots}
        self.message_processor = message_processor or IncomeMessageProcessor()

    async def handle_forwarded_summary(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        message = update.effective_message
        if not message or not message.text:
            return

        force_log(message, "BusinessForwardHandler", "DEBUG")

        if not self._is_trusted_forwarder(message):
            return

        origin_username = self._get_forward_origin(message) or ""

        try:
            await self.message_processor.store_message(
                chat_id=update.effective_chat.id,
                message_id=message.message_id,
                message_text=message.text,
                origin_username=origin_username,
                message_time=message.date,
            )
        except Exception as error:
            force_log(
                f"BusinessForwardHandler: error processing forwarded summary: {error}",
                "BusinessForwardHandler",
            )

    def _is_trusted_forwarder(self, message: Message) -> bool:
        if not message.from_user or not message.from_user.username:
            return False

        if getattr(message.from_user, "is_bot", False):
            return False

        sender_username = message.from_user.username.lstrip("@")
        if sender_username not in self.allowed_forwarders:
            return False

        return True

    def _get_forward_origin(self, message: Message) -> str:
        if not message.forward_origin:
            return ""

        from telegram._messageorigin import (
            MessageOriginUser,
            MessageOriginHiddenUser,
            MessageOriginChat,
            MessageOriginChannel,
        )

        origin = message.forward_origin

        if isinstance(origin, MessageOriginUser):
            return origin.sender_user.username.lstrip("@") if origin.sender_user.username else ""
        elif isinstance(origin, MessageOriginHiddenUser):
            return origin.sender_user_name.lstrip("@") if origin.sender_user_name else ""
        elif isinstance(origin, MessageOriginChat):
            return origin.sender_chat.username.lstrip("@") if origin.sender_chat.username else ""
        elif isinstance(origin, MessageOriginChannel):
            return origin.chat.username.lstrip("@") if origin.chat.username else ""

        return ""
