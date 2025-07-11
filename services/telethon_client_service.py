import os

from telethon import TelegramClient, events
from telethon.errors import PersistentTimestampInvalidError

from helper import extract_amount_and_currency, extract_trx_id
from models import ChatService, IncomeService


class TelethonClientService:
    def __init__(self):
        self.client = None
        self.service = IncomeService()

    async def start(self, username, api_id, api_hash):
        session_file = f"{username}.session"
        self.client = await self._init_client(username, api_id, api_hash, session_file)
        chat_service = ChatService()

        @self.client.on(events.NewMessage)  # type: ignore
        async def _new_message_listener(event):
            await self._handle_new_message(event, chat_service)

        await self.client.run_until_disconnected()  # type: ignore

    async def _init_client(self, username, api_id, api_hash, session_file):
        try:
            client = TelegramClient(username, int(api_id), api_hash)
            await client.connect()
            await client.start(phone=username)  # type: ignore
            print(f"Account {username} started...")
            return client
        except PersistentTimestampInvalidError:
            print(f"Session corrupted for {username}, removing session file...")
            if os.path.exists(session_file):
                os.remove(session_file)
            client = TelegramClient(username, int(api_id), api_hash)
            await client.connect()
            await client.start(phone=username)  # type: ignore
            print(f"Account {username} restarted with clean session...")
            return client
        except TimeoutError as e:
            print(f"Connection timeout for {username}: {e}")
            print("Will retry connection automatically...")
            # Let Telethon handle automatic reconnection
            raise
        except Exception as e:
            print(f"Error starting client for {username}: {e}")
            raise

    async def _handle_new_message(self, event, chat_service):
        # Check if this is a private chat (not a group)
        if event.is_private:
            await event.respond("សូមទាក់ទងទៅអ្នកគ្រប់គ្រង: https://t.me/HK_688")
            return

        currency, amount = extract_amount_and_currency(event.message.text)
        message_id: int = event.message.id
        trx_id: str | None = extract_trx_id(event.message.text)

        # Check for duplicate based on message_id first
        if await self.service.get_income_by_message_id(message_id):
            return

        # Check for duplicate based on trx_id only if trx_id exists
        if trx_id and await self.service.get_income_by_trx_id(
            trx_id, str(event.chat_id)
        ):
            return

        # Only require currency and amount, trx_id is optional
        if not (currency and amount):
            return

        # Check if chat exists, auto-register if not
        if not await chat_service.chat_exists(event.chat_id):
            if not await self._auto_register_chat(event, chat_service):
                return

        # Get chat info to check registration timestamp
        chat = await chat_service.get_chat_by_chat_id(str(event.chat_id))
        if not chat:
            return

        if not await self._is_message_after_chat_registration(event, chat):
            return

        # Let the income service handle shift creation automatically
        await self.service.insert_income(
            str(event.chat_id),  # Convert to string
            amount,
            currency,
            amount,
            message_id,
            event.message.text,
            trx_id,
            None,
        )

    async def _auto_register_chat(self, event, chat_service):
        try:
            chat_entity = await self.client.get_entity(event.chat_id)  # type: ignore
            chat_title = getattr(chat_entity, "title", f"Chat {event.chat_id}")
            success, _ = await chat_service.register_chat_id(
                event.chat_id, chat_title, None
            )
            if not success:
                print(f"Failed to auto-register chat {event.chat_id}")
                return False
            print(f"Auto-registered chat: {event.chat_id} ({chat_title})")
            return True
        except Exception as e:
            print(f"Error during chat auto-registration: {e}")
            return False

    async def _is_message_after_chat_registration(self, event, chat):
        from helper import DateUtils
        import pytz

        message_time = event.message.date
        if message_time.tzinfo is None:
            message_time = pytz.UTC.localize(message_time)

        chat_created = chat.created_at
        if chat_created.tzinfo is None:
            chat_created = DateUtils.localize_datetime(chat_created)
        chat_created_utc = chat_created.astimezone(pytz.UTC)

        if message_time < chat_created_utc:
            print(
                f"Ignoring message from {message_time} (before chat registration at {chat_created_utc})"
            )
            return False
        return True
