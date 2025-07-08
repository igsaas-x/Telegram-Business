import asyncio
import os

from telethon import TelegramClient, events

from handlers import EventHandler
from models import UserService, ChatService


class TelegramBotService:
    def __init__(self):
        self.bot: TelegramClient = None  # type: ignore
        self.event_handler = EventHandler()
        self.user_service = UserService()
        self.chat_service = ChatService()

    async def start(self, bot_token: str):
        self.bot = TelegramClient(
            "bot", int(os.getenv("API_ID")), os.getenv("API_HASH")  # type: ignore
        )  # type: ignore
        await self.bot.start(bot_token=bot_token)  # type: ignore
        self._register_event_handlers()

        try:
            print("Bot is running...")
            await self.bot.run_until_disconnected()  # type: ignore
        except asyncio.CancelledError:
            await self.bot.disconnect()  # type: ignore
            print("Bot stopped by user")

    def _register_event_handlers(self):
        @self.bot.on(events.NewMessage(pattern="/menu"))
        async def menu_handler(event):
            await self.event_handler.menu(event)

        # Register command handler
        @self.bot.on(events.NewMessage(pattern="/register"))
        async def register_handler(event):
            try:
                # Always insert user if not exists, regardless of chat_id existence
                sender = await event.get_sender()
                user = await self.user_service.create_user(sender)
                
                # Check if chat_id already exists
                existing_chat = await self.chat_service.get_chat_by_chat_id(str(event.chat_id))
                if existing_chat:
                    # Update the existing chat with the current user_id
                    if user and existing_chat.user_id != user.id:
                        await self.chat_service.update_chat_user_id(str(event.chat_id), user.id)
                        await event.respond(f"Chat ID {event.chat_id} is already registered. Updated with current user.")
                    else:
                        await event.respond(f"Chat ID {event.chat_id} is already registered.")
                    return

                await self.event_handler.register(event, user)
            except Exception as e:
                print(f"Error in register_handler: {e}")
                await event.respond("An error occurred during registration. Please try again.")

        # Callback query handler
        @self.bot.on(events.CallbackQuery())
        async def callback_handler(event):
            await self.event_handler.callback(event)

        # Message handler
        @self.bot.on(events.NewMessage())
        async def message_handler(event):
            await self.event_handler.message(event)
