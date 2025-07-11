import datetime
import logging
import os

from telethon import TelegramClient, events
from telethon.errors import PersistentTimestampInvalidError

from helper import extract_amount_and_currency, extract_trx_id
from models import ChatService, IncomeService


def force_log(message):
    """Write logs to telegram_bot.log since normal logging doesn't work"""
    with open("telegram_bot.log", "a") as f:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"{timestamp} - TelethonClient - INFO - {message}\n")
        f.flush()


logger = logging.getLogger(__name__)


class TelethonClientService:
    def __init__(self):
        self.client = None
        self.service = IncomeService()

    async def start(self, username, api_id, api_hash):
        session_file = f"{username}.session"

        # Handle persistent timestamp errors by removing corrupted session
        try:
            self.client = TelegramClient(username, int(api_id), api_hash)
            await self.client.connect()
            await self.client.start(phone=username)  # type: ignore
            logger.info(f"Account {username} started...")
        except PersistentTimestampInvalidError:
            logger.warning(f"Session corrupted for {username}, removing session file...")
            if os.path.exists(session_file):
                os.remove(session_file)

            # Recreate client with clean session
            self.client = TelegramClient(username, int(api_id), api_hash)
            await self.client.connect()
            await self.client.start(phone=username)  # type: ignore
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
            try:
                # Check if this is a private chat (not a group)
                if event.is_private:
                    await event.respond("សូមទាក់ទងទៅអ្នកគ្រប់គ្រង: https://t.me/HK_688")
                    return

                force_log(f"Processing message from chat {event.chat_id}: {event.message.text[:100]}...")
                currency, amount = extract_amount_and_currency(event.message.text)
                message_id: int = event.message.id
                trx_id: str | None = extract_trx_id(event.message.text)

                force_log(f"Extracted: currency={currency}, amount={amount}, trx_id={trx_id}")

                # Check for duplicate based on message_id first
                if await self.service.get_income_by_message_id(message_id):
                    force_log(f"Duplicate message_id {message_id}, skipping")
                    return

                # Check for duplicate based on trx_id only if trx_id exists
                if trx_id and await self.service.get_income_by_trx_id(trx_id, event.chat_id):
                    force_log(f"Duplicate trx_id {trx_id}, skipping")
                    return

                # Only require currency and amount, trx_id is optional
                if currency and amount:
                    
                    # Check if chat exists, auto-register if not
                    chat_registered_now = False
                    if not await chat_service.chat_exists(event.chat_id):
                        try:
                            # Get chat title for registration
                            chat_entity = await self.client.get_entity(event.chat_id)
                            chat_title = getattr(chat_entity, 'title', f"Chat {event.chat_id}")

                            # Register the chat without a specific user (user=None)
                            success, err_message = await chat_service.register_chat_id(event.chat_id, chat_title, None)

                            if not success:
                                # If registration failed, skip this message
                                logger.error(f"Failed to auto-register chat {event.chat_id}, {err_message}")
                                return

                            chat_registered_now = True
                            logger.info(f"Auto-registered chat: {event.chat_id} ({chat_title})")
                        except Exception as e:
                            logger.error(f"Error during chat auto-registration: {e}")
                            return

                # Get chat info to check registration timestamp
                chat = await chat_service.get_chat_by_chat_id(event.chat_id)
                if not chat:
                    return

                # Check if message was sent after chat registration (applies to all messages)
                from helper import DateUtils
                import pytz

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
                        f"Ignoring message from {message_time} (before chat registration at {chat_created_utc})")
                    return

                # Let the income service handle shift creation automatically
                force_log(f"Attempting to save income: chat_id={event.chat_id}, amount={amount}, currency={currency}")
                try:
                    await self.service.insert_income(
                        event.chat_id,  # Convert to string
                        amount,
                        currency,
                        amount,
                        message_id,
                        event.message.text,
                        trx_id,
                        # Don't pass shift_id - let auto-creation handle it
                    )
                    force_log(f"Successfully saved income record for message {message_id}")
                except Exception as income_error:
                    force_log(f"ERROR saving income: {income_error}")
                    raise income_error
                else:
                    force_log(f"Message doesn't contain valid currency/amount: {event.message.text[:100]}...")
            except Exception as e:
                force_log(f"ERROR in message processing: {e}")

        await self.client.run_until_disconnected()  # type: ignore
