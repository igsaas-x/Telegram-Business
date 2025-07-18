import os

import pytz
from telethon import TelegramClient, events
from telethon.errors import PersistentTimestampInvalidError

# Check if message was sent after chat registration (applies to all messages)
from helper import DateUtils
from helper import extract_amount_and_currency, extract_trx_id
from helper.logger_utils import force_log
from models import ChatService, IncomeService
from services.message_verification_scheduler import MessageVerificationScheduler


class TelethonClientService:
    def __init__(self):
        self.client = None
        self.service = IncomeService()
        self.scheduler = None

    async def get_username_by_phone(self, phone_number: str) -> str | None:
        """
        Get Telegram username by phone number.
        
        Args:
            phone_number: The phone number to search for (with or without country code)
            
        Returns:
            Username string if found, None if not found or error occurs
        """
        if not self.client:
            force_log("Client not initialized. Cannot get username by phone.")
            return None
            
        try:
            # Clean phone number - remove spaces, dashes, plus signs
            clean_phone = phone_number.replace(" ", "").replace("-", "").replace("+", "")
            
            # Try to resolve the user by phone number
            try:
                user = await self.client.get_entity(f"+{clean_phone}")
                if hasattr(user, 'username') and user.username:
                    force_log(f"Found username '{user.username}' for phone {phone_number}")
                    return user.username
                else:
                    force_log(f"User found for phone {phone_number} but no username set")
                    return None
            except Exception as e:
                # Try without the plus sign if the first attempt failed
                try:
                    user = await self.client.get_entity(clean_phone)
                    if hasattr(user, 'username') and user.username:
                        force_log(f"Found username '{user.username}' for phone {phone_number}")
                        return user.username
                    else:
                        force_log(f"User found for phone {phone_number} but no username set")
                        return None
                except Exception as e2:
                    force_log(f"Could not find user for phone {phone_number}: {e2}")
                    return None
                    
        except Exception as e:
            force_log(f"Error getting username by phone {phone_number}: {e}")
            return None

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
        
        # Initialize and start the message verification scheduler
        self.scheduler = MessageVerificationScheduler(self.client)
        force_log("Starting message verification scheduler...")
        
        @self.client.on(events.NewMessage)  # type: ignore
        async def _new_message_listener(event):
            force_log(f"=== NEW MESSAGE EVENT TRIGGERED ===")
            force_log(f"Chat ID: {event.chat_id}, Message: '{event.message.text}'")

            try:
                sender = await event.get_sender()
                is_bot = getattr(sender, 'bot', False)
                # Check if this is a private chat (not a group)
                if event.is_private and not is_bot:
                    force_log(f"Private chat detected, sending auto-response")
                    await event.respond("សូមទាក់ទងទៅអ្នកគ្រប់គ្រង: https://t.me/HK_688")
                    return

                # Only listen to bot messages, ignore human messages
                if not is_bot:
                    force_log(f"Message from human user, ignoring")
                    return
                
                # Ignore specific bot: AutosumBusinessBot
                if getattr(sender, 'username', '') == 'AutosumBusinessBot':
                    force_log(f"Message from AutosumBusinessBot, ignoring")
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

                # Use comprehensive duplicate check (chat_id + trx_id + message_id)
                is_duplicate = await self.service.check_duplicate_transaction(event.chat_id, trx_id, message_id)
                if is_duplicate:
                    force_log(f"Duplicate transaction found for chat_id={event.chat_id}, trx_id={trx_id}, message_id={message_id}, skipping")
                    return

                force_log(f"No duplicates found - proceeding with income processing...")

                # Check if chat exists, auto-register if not
                # force_log(f"Checking if chat {event.chat_id} exists...")
                # if not await chat_service.chat_exists(event.chat_id):
                #     force_log(f"Chat {event.chat_id} not registered, auto-registering...")
                #     try:
                #         # Get chat title for registration
                #         chat_entity = await self.client.get_entity(event.chat_id)
                #         chat_title = getattr(chat_entity, 'title', f"Chat {event.chat_id}")
                #
                #         # Register the chat without a specific user (user=None)
                #         success, err_message = await chat_service.register_chat_id(event.chat_id, chat_title, None)
                #
                #         if not success:
                #             force_log(f"Failed to auto-register chat {event.chat_id}: {err_message}")
                #             return
                #
                #         force_log(f"Auto-registered chat: {event.chat_id} ({chat_title})")
                #     except Exception as e:
                #         force_log(f"Error during chat auto-registration: {e}")
                #         return

                # Get chat info to check registration timestamp
                force_log(f"Getting chat info for chat_id: {event.chat_id}")
                chat = await chat_service.get_chat_by_chat_id(event.chat_id)
                if not chat:
                    force_log(f"Chat {event.chat_id} not found in database!")
                    return

                force_log(f"Checking message timestamp vs chat registration timestamp")
                # Get message timestamp (Telethon provides it as UTC datetime)
                message_time = event.message.date
                if message_time.tzinfo is None:
                    message_time = pytz.UTC.localize(message_time)

                # Convert chat created_at to UTC for comparison
                chat_created = chat.created_at
                if chat_created.tzinfo is None:
                    chat_created = DateUtils.localize_datetime(chat_created)
                chat_created_utc = chat_created.astimezone(pytz.UTC)

                force_log(f"Message time: {message_time}, Chat created: {chat_created_utc}")
                # Ignore messages sent before chat registration
                if message_time < chat_created_utc:
                    force_log(f"Ignoring message from {message_time} (before chat registration at {chat_created_utc})")
                    return

                force_log(f"Message timestamp verified, proceeding to save income...")

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
                        None,  # shift_id
                        chat.enable_shift  # enable_shift
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

        # Start both the client and scheduler concurrently
        import asyncio
        await asyncio.gather(
            self.client.run_until_disconnected(),  # type: ignore
            self.scheduler.start_scheduler()
        )