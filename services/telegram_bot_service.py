import asyncio
import logging
import os

from telethon import TelegramClient, events

from handlers import EventHandler
from models import UserService, ChatService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("telegram_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


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
            logger.info("Bot is running...")
            print("Bot is running...")
            await self.bot.run_until_disconnected()  # type: ignore
        except asyncio.CancelledError:
            await self.bot.disconnect()  # type: ignore
            logger.info("Bot stopped by user")
            print("Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot crashed with error: {e}")
            print(f"Bot crashed with error: {e}")
            raise

    def _register_event_handlers(self):
        @self.bot.on(events.NewMessage(pattern="/menu"))
        async def menu_handler(event):
            try:
                await self.event_handler.menu(event)
            except Exception as e:
                logger.error(f"Error in menu_handler: {e}")
                await event.respond("An error occurred. Please try again.")

        # Register command handler
        @self.bot.on(events.NewMessage(pattern="/register"))
        async def register_handler(event):
            try:
                logger.info(f"Registration attempt from chat {event.chat_id}")
                # Always insert user if not exists, regardless of chat_id existence
                sender = await event.get_sender()
                
                # Check if sender is anonymous
                if not sender or not hasattr(sender, 'id') or sender.id is None:
                    logger.warning(f"Anonymous user registration attempt in chat {event.chat_id}")
                    await event.respond("⚠️ Registration failed: You must be a non-anonymous user to register this chat. Please disable anonymous mode and try again.")
                    return
                
                logger.info(f"Registration request from user {sender.id} in chat {event.chat_id}")
                user = await self.user_service.create_user(sender)
                
                # Check if chat_id already exists
                existing_chat = await self.chat_service.get_chat_by_chat_id(str(event.chat_id))
                if existing_chat:
                    # Update the existing chat with the current user_id
                    if user and existing_chat.user_id != user.id:
                        logger.info(f"Updated existing chat {event.chat_id} with new user {user.id}")
                        await self.chat_service.update_chat_user_id(str(event.chat_id), user.id)
                        await event.respond(f"Chat ID {event.chat_id} is already registered. Updated with current user.")
                    else:
                        logger.info(f"Chat {event.chat_id} already registered with same user")
                        await event.respond(f"Chat ID {event.chat_id} is already registered.")
                    return

                logger.info(f"Proceeding with new registration for chat {event.chat_id}")
                await self.event_handler.register(event, user)
            except Exception as e:
                logger.error(f"Error in register_handler: {e}", exc_info=True)
                await event.respond("An error occurred during registration. Please try again.")

        # Contact us command handler
        @self.bot.on(events.NewMessage(pattern="/contact_us"))
        async def contact_us_handler(event):
            try:
                message = "សូមទាក់ទងយើងខ្ញុំតាមរយៈ Telegram៖ https://t.me/HK_688"
                await event.respond(message)
            except Exception as e:
                logger.error(f"Error in contact_us_handler: {e}")
                await event.respond("An error occurred. Please try again.")

        # Callback query handler
        @self.bot.on(events.CallbackQuery())
        async def callback_handler(event):
            try:
                await self.event_handler.callback(event)
            except Exception as e:
                logger.error(f"Error in callback_handler: {e}")
                await event.respond("An error occurred. Please try again.")

        # Message handler
        @self.bot.on(events.NewMessage())
        async def message_handler(event):
            try:
                await self.event_handler.message(event)
            except Exception as e:
                logger.error(f"Error in message_handler: {e}")
                # Don't respond here as it might cause message loops for regular messages
