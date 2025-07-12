import logging
import os
import pytz
from typing import Optional

from telethon import TelegramClient, events
from telethon.events import NewMessage
from telethon.errors import PersistentTimestampInvalidError
from helper import DateUtils, extract_amount_and_currency, extract_trx_id
from models import ChatService, IncomeService, MessagesModel
from helper import CredentialLoader

logger = logging.getLogger(__name__)


class TelethonClientService:
    def __init__(self):
        self.client: Optional[TelegramClient] = None
        self.service = IncomeService()
        self.messages_service = MessagesModel()
        self.config = CredentialLoader()
        self.config.load_credentials()

    def _is_notification_bot_message(self, event: NewMessage.Event) -> bool:
        """Check if the message is a notification bot message

        Args:
            event: The NewMessage event from Telethon

        Returns:
            bool: True if the message is from a bot in a private chat and not from our bot
        """
        return (
            event.sender is not None
            and not event.is_private
            and event.sender.username != self.config.bot_name
        )

    async def start(self, username: str, api_id: str, api_hash: str):
        session_file = f"{username}.session"

        # Handle persistent timestamp errors by removing corrupted session
        try:
            self.client = TelegramClient(username, int(api_id), api_hash)
            await self.client.connect()
            await self.client.start(phone=username)
            logger.info(f"Account {username} started...")
        except PersistentTimestampInvalidError:
            logger.warning(
                f"Session corrupted for {username}, removing session file..."
            )
            if os.path.exists(session_file):
                os.remove(session_file)

            # Recreate client with clean session
            self.client = TelegramClient(username, int(api_id), api_hash)
            await self.client.connect()
            await self.client.start(phone=username)
            logger.info(f"Account {username} restarted with clean session...")
        except TimeoutError as e:
            logger.warning(f"Connection timeout for {username}: {e}")
            logger.info("Will retry connection automatically...")
            # Let Telethon handle automatic reconnection
        except Exception as e:
            logger.error(f"Error starting client for {username}: {e}")
            raise

        chat_service = ChatService()

        # @self.client.on(events.NewMessage(pattern="/verify"))
        # async def _verify_current_date_report(event):
        #     chat = event.chat_id
        #     today = DateUtils.today()
        #     yesterday = today - timedelta(days=1)
        #     start_of_yesterday = DateUtils.start_of_day(yesterday)

        #     last_msg = await self.service.get_last_yesterday_message(start_of_yesterday)
        #     min_id = int(getattr(last_msg, "message_id", 0)) if last_msg else 0

        #     # Get when this client was added to the group
        #     try:
        #         me = await self.client.get_me()
        #         participants = await self.client.get_participants(chat)
        #         my_participant = next((p for p in participants if p.id == me.id), None)

        #         # If we can't find when we were added, use current time to avoid historical messages
        #         join_time = getattr(my_participant, 'date', DateUtils.now()) if my_participant else DateUtils.now()
        #     except Exception:
        #         # If we can't get join time, use current time as fallback
        #         join_time = DateUtils.now()

        #     incomes = []
        #     processed_ids = set()

        #     async for msg in self.client.iter_messages(  # type: ignore
        #         chat, search="paid by", min_id=min_id
        #     ):
        #         # Skip messages sent before we joined the group
        #         if msg.date < join_time:
        #             continue
        #         if not (msg.text and msg.date) or msg.id in processed_ids:
        #             continue

        #         currency, amount = extract_amount_and_currency(msg.text)
        #         trx_id = extract_trx_id(msg.text)
        #         processed_ids.add(msg.id)

        #         if not (currency and amount):
        #             continue

        #         currency_code = next(
        #             (c.name for c in CurrencyEnum if c.value == currency), None
        #         )
        #         if not currency_code:
        #             continue

        #         try:
        #             amount_value = float(str(amount).replace(",", "").replace(" ", ""))
        #         except Exception:
        #             continue

        #         incomes.append(
        #             IncomeBalance(
        #                 amount=amount_value,
        #                 chat_id=chat,
        #                 currency=currency_code,
        #                 original_amount=amount_value,
        #                 income_date=msg.date,
        #                 message_id=msg.id,
        #                 message=msg.text,
        #                 trx_id=trx_id,
        #             )
        #         )

        #     summary = total_summary_report(incomes, "របាយការណ៍សរុបប្រចាំថ្ងៃនេះ")
        #     await event.client.send_message(chat, summary)

        @self.client.on(events.NewMessage)  # type: ignore
        async def _new_message_listener(event):
            chat_id = int(event.chat_id)

            # Check if this is a private chat (not a group)
            if event.is_private:
                await event.respond("សូមទាក់ទងទៅអ្នកគ្រប់គ្រង: https://t.me/HK_688")
                return

            currency, amount = extract_amount_and_currency(event.message.text or "")
            message_id: int = event.message.id
            trx_id: str | None = extract_trx_id(event.message.text or "")

            # Check for duplicate based on message_id first
            if await self.service.get_income_by_message_id(message_id):
                return

            # Check for duplicate based on trx_id only if trx_id exists
            if trx_id and await self.service.get_income_by_trx_id(trx_id, chat_id):
                return

                # Save the message to the database
            if self._is_notification_bot_message(event) and trx_id:
                self.messages_service.save(
                    chat_id=chat_id,
                    message_id=event.message.id,
                    original_message=event.message.text or "",
                )

            # Only require currency and amount, trx_id is optional
            if currency and amount:
                # Check if chat exists, auto-register if not
                chat_registered_now = False
                if not await chat_service.chat_exists(chat_id):
                    try:
                        if not self.client:
                            logger.error("Client not initialized")
                            return

                        # Get chat title for registration
                        chat_entity = await self.client.get_entity(chat_id)
                        chat_title = getattr(chat_entity, "title", f"Chat {chat_id}")

                        # Register the chat without a specific user (user=None)
                        success, err_message = await chat_service.register_chat_id(
                            chat_id, chat_title, None
                        )

                        if not success:
                            # If registration failed, skip this message
                            logger.error(
                                f"Failed to auto-register chat {chat_id}, {err_message}"
                            )
                            return

                        logger.info(f"Auto-registered chat: {chat_id} ({chat_title})")
                    except Exception as e:
                        logger.error(f"Error during chat auto-registration: {e}")
                        return

                # Get chat info to check registration timestamp
                chat = await chat_service.get_chat_by_chat_id(chat_id)
                if not chat:
                    return

                # Check if message was sent after chat registration (applies to all messages)

                # Get message timestamp (Telethon provides it as UTC datetime)
                message_time = event.message.date
                if message_time.tzinfo is None:
                    message_time = pytz.UTC.localize(message_time)

                # Convert chat created_at to UTC for comparison
                chat_created = chat.created_at
                if chat_created.tzinfo is None:
                    chat_created = DateUtils.localize_datetime(chat_created)
                chat_created_utc = chat_created.astimezone(pytz.UTC)

                # Ignore messages sent before chat registration
                if message_time < chat_created_utc:
                    logger.debug(
                        f"Ignoring message from {message_time} (before chat registration at {chat_created_utc})"
                    )
                    return

                # Let the income service handle shift creation automatically
                await self.service.insert_income(
                    chat_id,  # Convert to string
                    amount,
                    currency,
                    amount,
                    message_id,
                    event.message.text,
                    trx_id,
                    # Don't pass shift_id - let auto-creation handle it
                )

        await self.client.run_until_disconnected()  # type: ignore
