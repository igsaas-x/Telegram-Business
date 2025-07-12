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
            force_log(f"Account {username} started...")
        except PersistentTimestampInvalidError:
            force_log(f"Session corrupted for {username}, removing session file...")
            if os.path.exists(session_file):
                os.remove(session_file)
            
            # Recreate client with clean session
            self.client = TelegramClient(username, int(api_id), api_hash)
            await self.client.connect()
            await self.client.start(phone=username)  # type: ignore
            force_log(f"Account {username} restarted with clean session...")
        except TimeoutError as e:
            force_log(f"Connection timeout for {username}: {e}")
            force_log("Will retry connection automatically...")
            # Let Telethon handle automatic reconnection
        except Exception as e:
            force_log(f"Error starting client for {username}: {e}")
            raise

        chat_service = ChatService()

        # Add a startup log to confirm client is ready
        force_log("Telethon client event handlers registered successfully")
        
        @self.client.on(events.NewMessage)  # type: ignore
        async def _new_message_listener(event):
            force_log(f"=== NEW MESSAGE EVENT TRIGGERED ===")
            force_log(f"Chat ID: {event.chat_id}, Message: '{event.message.text}'")
            
            try:
                # Check if this is a private chat (not a group)
                if event.is_private:
                    force_log(f"Private chat detected, sending auto-response")
                    await event.respond("សូមទាក់ទងទៅអ្នកគ្រប់គ្រង: https://t.me/HK_688")
                    return

                # Skip if no message text
                if not event.message.text:
                    force_log("No message text, skipping")
                    return

                force_log(f"Processing message from chat {event.chat_id}: {event.message.text}")
                currency, amount = extract_amount_and_currency(event.message.text)
                message_id: int = event.message.id
                trx_id: str | None = extract_trx_id(event.message.text)
                
                force_log(f"Extracted: currency={currency}, amount={amount}, trx_id={trx_id}")

                # Skip if no valid currency/amount (do this check early)
                if not (currency and amount):
                    force_log(f"No valid currency/amount found in message: {event.message.text}")
                    return

                force_log(f"Valid currency and amount found, checking duplicates...")

                # Check for duplicate based on message_id first
                force_log(f"Checking for duplicate message_id: {message_id}")
                is_duplicate_msg = await self.service.get_income_by_message_id(message_id)
                force_log(f"Message ID duplicate check result: {is_duplicate_msg}")
                if is_duplicate_msg:
                    force_log(f"Duplicate message_id {message_id} found, skipping")
                    return

                # Check for duplicate based on trx_id only if trx_id exists
                is_duplicate_trx = False
                if trx_id:
                    force_log(f"Checking for duplicate trx_id: {trx_id} in chat: {event.chat_id}")
                    is_duplicate_trx = await self.service.get_income_by_trx_id(trx_id, event.chat_id)
                    force_log(f"Transaction ID duplicate check result: {is_duplicate_trx}")
                    if is_duplicate_trx:
                        force_log(f"Duplicate trx_id {trx_id} found for chat {event.chat_id}, skipping")
                        return
                else:
                    force_log(f"No trx_id to check for duplicates")

                force_log(f"No duplicates found - proceeding with income processing...")

                # Check if chat exists, auto-register if not
                force_log(f"Checking if chat {event.chat_id} exists...")
                if not await chat_service.chat_exists(event.chat_id):
                    force_log(f"Chat {event.chat_id} not registered, auto-registering...")
                    try:
                        # Get chat title for registration
                        chat_entity = await self.client.get_entity(event.chat_id)
                        chat_title = getattr(chat_entity, 'title', f"Chat {event.chat_id}")

                        # Register the chat without a specific user (user=None)
                        success, err_message = await chat_service.register_chat_id(event.chat_id, chat_title, None)

                        if not success:
                            force_log(f"Failed to auto-register chat {event.chat_id}: {err_message}")
                            return

                        force_log(f"Auto-registered chat: {event.chat_id} ({chat_title})")
                    except Exception as e:
                        force_log(f"Error during chat auto-registration: {e}")
                        return

                # Get chat info to check registration timestamp
                force_log(f"Getting chat info for chat_id: {event.chat_id}")
                chat = await chat_service.get_chat_by_chat_id(event.chat_id)
                if not chat:
                    force_log(f"Chat {event.chat_id} not found in database after registration!")
                    return

                # Skip timestamp check for now to simplify debugging
                force_log(f"Chat found, proceeding to save income...")

                # Let the income service handle shift creation automatically
                force_log(f"Attempting to save income: chat_id={event.chat_id}, amount={amount}, currency={currency}")
                try:
                    result = await self.service.insert_income(
                        event.chat_id,
                        amount,
                        currency,
                        amount,
                        message_id,
                        event.message.text,
                        trx_id,
                        chat.enable_shift
                    )
                    force_log(f"Successfully saved income record with id={result.id} for message {message_id}")
                except Exception as income_error:
                    force_log(f"ERROR saving income: {income_error}")
                    import traceback
                    force_log(f"Traceback: {traceback.format_exc()}")

            except Exception as e:
                force_log(f"ERROR in message processing: {e}")
                import traceback
                force_log(f"Traceback: {traceback.format_exc()}")

        await self.client.run_until_disconnected()  # type: ignore