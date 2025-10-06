from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import pytz

from helper import (
    DateUtils,
    extract_amount_and_currency,
    extract_s7pos_amount_and_currency,
    extract_s7days_amount_and_currency,
    extract_shifts_with_breakdown,
    extract_trx_id,
)
from helper.logger_utils import force_log
from services import ChatService, IncomeService


class IncomeMessageProcessor:
    """Shared helper to persist income messages across entrypoints."""

    def __init__(
            self,
            income_service: Optional[IncomeService] = None,
            chat_service: Optional[ChatService] = None,
    ) -> None:
        self.income_service = income_service or IncomeService()
        self.chat_service = chat_service or ChatService()

    async def store_message(
            self,
            *,
            chat_id: int,
            message_id: int,
            message_text: str,
            origin_username: str,
            message_time: datetime,
            trx_id: Optional[str] = None,
    ):
        """Parse and persist a bank notification message."""

        force_log(
            f"Processor received message {message_id} from chat {chat_id} by '{origin_username}'",
            "IncomeMessageProcessor",
        )

        if not message_text:
            force_log("Message text empty, skipping", "IncomeMessageProcessor")
            return None

        shifts_breakdown = None

        # Determine amount & currency based on origin bot
        if origin_username == "s7pos_bot":
            currency, amount = extract_s7pos_amount_and_currency(message_text)
        elif origin_username == "S7days777" or origin_username == "payment_bk_bot":
            # Try to extract shifts with breakdown first (for messages with multiple shifts)
            shifts_breakdown = extract_shifts_with_breakdown(message_text)
            if shifts_breakdown:
                force_log(
                    f"Extracted {len(shifts_breakdown)} shifts with breakdown",
                    "IncomeMessageProcessor",
                )
            # If shifts_breakdown has "total" fields, use sum of those instead
            if shifts_breakdown and any("total" in shift for shift in shifts_breakdown):
                total_amount = sum(shift.get("total", 0) for shift in shifts_breakdown)
                currency = "$"
                amount = total_amount
                force_log(
                    f"Using sum of shift totals: {amount}",
                    "IncomeMessageProcessor",
                )
            else:
                currency, amount = extract_s7days_amount_and_currency(message_text)
        else:
            currency, amount = extract_amount_and_currency(message_text)

        if not (currency and amount):
            force_log(
                f"No valid currency/amount found in message {message_id}, skipping",
                "IncomeMessageProcessor",
            )
            return None

        trx_id = trx_id or extract_trx_id(message_text)

        is_duplicate = await self.income_service.check_duplicate_transaction(
            chat_id, trx_id, message_id
        )
        if is_duplicate:
            force_log(
                f"Duplicate detected for chat_id={chat_id}, trx_id={trx_id}, message_id={message_id}",
                "IncomeMessageProcessor",
            )
            return None

        chat = await self.chat_service.get_chat_by_chat_id(chat_id)
        if not chat:
            force_log(f"Chat {chat_id} not registered, skipping", "IncomeMessageProcessor")
            return None

        # Normalise timestamps and enforce registration buffer
        msg_time = message_time
        if msg_time.tzinfo is None:
            msg_time = pytz.UTC.localize(msg_time)
        else:
            msg_time = msg_time.astimezone(pytz.UTC)

        chat_created = chat.created_at
        if chat_created.tzinfo is None:
            chat_created = DateUtils.localize_datetime(chat_created)
        chat_created_utc = chat_created.astimezone(pytz.UTC)

        buffer_time = chat_created_utc - timedelta(minutes=1)
        if msg_time < buffer_time:
            force_log(
                f"Message timestamp {msg_time} before registration buffer {buffer_time}, skipping",
                "IncomeMessageProcessor",
            )
            return None

        force_log(
            f"Persisting income for chat {chat_id}: amount={amount}, currency={currency}",
            "IncomeMessageProcessor",
        )

        result = await self.income_service.insert_income(
            chat_id,
            amount,
            currency,
            amount,
            message_id,
            message_text,
            trx_id,
            0,
            chat.enable_shift,
            origin_username,
            None,
            shifts_breakdown,
        )

        force_log(
            f"Stored income id={result.id} for message {message_id}",
            "IncomeMessageProcessor",
        )

        return result
