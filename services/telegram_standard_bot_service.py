import asyncio
import logging
import os

from telethon import TelegramClient, events

from handlers import EventHandler
from models import User
from services import UserService, ChatService
from services.private_bot_group_binding_service import PrivateBotGroupBindingService

# Use the logging configuration from main_bots_only.py
# Don't call basicConfig() here as it only works once per process
logger = logging.getLogger(__name__)


class TelegramBotService:
    def __init__(self):
        self.bot: TelegramClient = None  # type: ignore
        self.event_handler = EventHandler()
        self.user_service = UserService()
        self.chat_service = ChatService()
        
        logger.info("TelegramBotService initialized")

    async def send_message_to_chat(self, chat_id: int, message: str):
        """
        Send a message to a specific chat
        
        Args:
            chat_id: The chat ID to send the message to
            message: The message text to send
        """
        try:
            if self.bot:
                await self.bot.send_message(chat_id, message)
                logger.info(f"Message sent to chat {chat_id}: {message[:50]}...")
            else:
                logger.info("Bot is not initialized, cannot send message")
        except Exception as e:
            logger.info(f"Failed to send message to chat {chat_id}: {str(e)}")

    async def start(self, bot_token: str):
        logger.info("TelegramBotService starting...")
        self.bot = TelegramClient(
            "bot", int(os.getenv("API_ID1")), os.getenv("API_HASH1")  # type: ignore
        )  # type: ignore
        await self.bot.start(bot_token=bot_token)  # type: ignore
        self._register_event_handlers()

        try:
            logger.info("TelegramBotService is running...")
            await self.bot.run_until_disconnected()  # type: ignore
        except asyncio.CancelledError:
            await self.bot.disconnect()  # type: ignore
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.info(f"Bot crashed with error: {e}")
            raise

    def _register_event_handlers(self):
        logger.info("Registering event handlers for TelegramBotService")
        
        @self.bot.on(events.NewMessage(pattern="/menu"))
        async def menu_handler(event):
            # Try different logging approaches
            print(f"PRINT: Menu handler triggered - Chat ID: {event.chat_id}")
            logging.getLogger(__name__).info(f"DIRECT: Menu handler triggered - Chat ID: {event.chat_id}")
            logger.info(f"🍔 Menu handler triggered - Chat ID: {event.chat_id}")
            try:
                # Check if this is a private chat
                if event.is_private:
                    await event.respond("❌ This bot only works in groups. Please add this bot to a group to use it.")
                    return

                # Check if this group is bound to a private chat
                chat = await self.chat_service.get_chat_by_chat_id(event.chat_id)
                if chat:
                    private_chats = PrivateBotGroupBindingService.get_private_chats_for_group(chat.id)
                else:
                    private_chats = None
                if private_chats:
                    message = f"""សូមប្រើPrivate Groupដើម្បីបូក
                    """
                    await event.respond(message)
                    return

                await self.event_handler.menu(event)
            except Exception as e:
                logger.info(f"Error in menu_handler: {e}")
                await event.respond("An error occurred. Please try again.")

        # Register command handler
        @self.bot.on(events.NewMessage(pattern="/register"))
        async def register_handler(event):
            try:
                logger.info(f"Registration attempt from chat {event.chat_id}")

                # Check if this is a private chat
                if event.is_private:
                    await event.respond("❌ This bot only works in groups. Please add this bot to a group to use it.")
                    return

                # Always insert user if not exists, regardless of chat_id existence
                sender = await event.get_sender()

                registered_user: User | None = None
                # Check if sender is anonymous
                if sender and hasattr(sender, "id") or sender.id is None:
                    registered_user = await self.user_service.create_user(sender)
                    logger.info(
                        f"Registration request from user {sender.id} in chat {event.chat_id}"
                    )

                # Check if chat_id already exists
                existing_chat = await self.chat_service.get_chat_by_chat_id(
                    event.chat_id
                )
                if existing_chat:
                    # Update the existing chat with the current user_id
                    if registered_user and existing_chat.user_id != registered_user.id:
                        logger.info(
                            f"Updated existing chat {event.chat_id} with new user {registered_user.id}"
                        )
                        await self.chat_service.update_chat_user_id(
                            event.chat_id, registered_user.id
                        )
                        await event.respond(
                            f"Chat ID {event.chat_id} is already registered. Updated with current user."
                        )
                    else:
                        logger.info(
                            f"Chat {event.chat_id} already registered with same user"
                        )
                        await event.respond(
                            f"Chat ID {event.chat_id} is already registered with the same user."
                        )
                    return

                logger.info(f"Proceeding with new registration for chat {event.chat_id}")
                await self.event_handler.register(event, registered_user)
            except Exception as e:
                print(f"Error on registration {e}")
                logger.info(f"Error in register_handler: {e}")
                await event.respond(
                    "An error occurred during registration. Please try again."
                )

        # Contact us command handler
        @self.bot.on(events.NewMessage(pattern="/contact_us"))
        async def contact_us_handler(event):
            try:
                message = "សូមទាក់ទងយើងខ្ញុំតាមរយៈ Telegram៖ https://t.me/HK_688"
                await event.respond(message)
            except Exception as e:
                logger.info(f"Error in contact_us_handler: {e}")
                await event.respond("An error occurred. Please try again.")

        # Callback query handler
        @self.bot.on(events.CallbackQuery())
        async def callback_handler(event):
            try:
                await self.event_handler.callback(event)
            except Exception as e:
                print(f"Error in callback_handler: {e}")
                logger.info(f"Error in callback_handler: {e}")
                await event.respond("An error occurred. Please try again.")

        # Chat migration handler - only handle migrate_to_chat_id to avoid duplicates
        @self.bot.on(events.NewMessage())
        async def migration_handler(event):
            try:
                # Debug: Log all messages here
                logger.info(f"📨 TelegramBotService received message: '{event.message.text}' from chat {event.chat_id}")
                
                # Only handle migrate_to_chat_id (from old group) to avoid duplicate processing
                if (
                        hasattr(event.message, "migrate_to_chat_id")
                        and event.message.migrate_to_chat_id
                ):
                    old_chat_id = event.chat_id
                    new_chat_id = event.message.migrate_to_chat_id

                    logger.info(
                        f"Chat migration detected: {old_chat_id} -> {new_chat_id}"
                    )

                    # Migrate the chat_id in the database
                    success = await self.chat_service.migrate_chat_id(
                        old_chat_id, new_chat_id
                    )

                    if success:
                        logger.info(
                            f"Successfully migrated chat data from {old_chat_id} to {new_chat_id}"
                        )
                    else:
                        logger.info(
                            f"Failed to migrate chat data from {old_chat_id} to {new_chat_id}"
                        )

                    return  # Don't process this message further

                # If not a migration event, process normally
                await self.event_handler.message(event)
            except Exception as e:
                logger.info(f"Error in migration_handler: {e}")
                # Don't respond here as it might cause message loops for regular messages
        
        logger.info("✅ All event handlers registered successfully for TelegramBotService")
