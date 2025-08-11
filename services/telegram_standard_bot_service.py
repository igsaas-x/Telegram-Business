import asyncio
import os

from telethon import TelegramClient, events

from handlers import EventHandler
from helper.logger_utils import force_log
from models import User
from services import UserService, ChatService
from services.private_bot_group_binding_service import PrivateBotGroupBindingService


class TelegramBotService:
    def __init__(self):
        self.bot: TelegramClient = None  # type: ignore
        self.event_handler = EventHandler()
        self.user_service = UserService()
        self.chat_service = ChatService()

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
                force_log(f"Message sent to chat {chat_id}: {message[:50]}...")
            else:
                force_log("Bot is not initialized, cannot send message")
        except Exception as e:
            force_log(f"Failed to send message to chat {chat_id}: {str(e)}")

    async def start(self, bot_token: str):
        self.bot = TelegramClient(
            "bot", int(os.getenv("API_ID1")), os.getenv("API_HASH1")  # type: ignore
        )  # type: ignore
        await self.bot.start(bot_token=bot_token)  # type: ignore
        self._register_event_handlers()

        try:
            force_log("Bot is running...")
            await self.bot.run_until_disconnected()  # type: ignore
        except asyncio.CancelledError:
            await self.bot.disconnect()  # type: ignore
            force_log("Bot stopped by user")
        except Exception as e:
            force_log(f"Bot crashed with error: {e}")
            raise

    def _register_event_handlers(self):
        @self.bot.on(events.NewMessage(pattern="/menu"))
        async def menu_handler(event):
            try:
                # Check if this is a private chat
                if event.is_private:
                    await event.respond("❌ This bot only works in groups. Please add this bot to a group to use it.")
                    return
                
                # Check if this group is bound to a private chat
                private_chats = PrivateBotGroupBindingService.get_private_chats_for_group(event.chat_id)
                if private_chats:
                    message = f"""
🔗 This group is already bound to private chat(s).

For reports and management, please check the bound private chat(s).

Private chat IDs: {', '.join(map(str, private_chats))}
                    """
                    await event.respond(message)
                    return
                
                await self.event_handler.menu(event)
            except Exception as e:
                force_log(f"Error in menu_handler: {e}")
                await event.respond("An error occurred. Please try again.")

        # Register command handler
        @self.bot.on(events.NewMessage(pattern="/register"))
        async def register_handler(event):
            try:
                force_log(f"Registration attempt from chat {event.chat_id}")
                
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
                    force_log(
                        f"Registration request from user {sender.id} in chat {event.chat_id}"
                    )

                # Check if chat_id already exists
                existing_chat = await self.chat_service.get_chat_by_chat_id(
                    event.chat_id
                )
                if existing_chat:
                    # Update the existing chat with the current user_id
                    if registered_user and existing_chat.user_id != registered_user.id:
                        force_log(
                            f"Updated existing chat {event.chat_id} with new user {registered_user.id}"
                        )
                        await self.chat_service.update_chat_user_id(
                            event.chat_id, registered_user.id
                        )
                        await event.respond(
                            f"Chat ID {event.chat_id} is already registered. Updated with current user."
                        )
                    else:
                        force_log(
                            f"Chat {event.chat_id} already registered with same user"
                        )
                        await event.respond(
                            f"Chat ID {event.chat_id} is already registered with the same user."
                        )
                    return

                force_log(f"Proceeding with new registration for chat {event.chat_id}")
                await self.event_handler.register(event, registered_user)
            except Exception as e:
                print(f"Error on registration {e}")
                force_log(f"Error in register_handler: {e}")
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
                force_log(f"Error in contact_us_handler: {e}")
                await event.respond("An error occurred. Please try again.")

        # Callback query handler
        @self.bot.on(events.CallbackQuery())
        async def callback_handler(event):
            try:
                await self.event_handler.callback(event)
            except Exception as e:
                print(f"Error in callback_handler: {e}")
                force_log(f"Error in callback_handler: {e}")
                await event.respond("An error occurred. Please try again.")

        # Chat migration handler - only handle migrate_to_chat_id to avoid duplicates
        @self.bot.on(events.NewMessage())
        async def migration_handler(event):
            try:
                # Only handle migrate_to_chat_id (from old group) to avoid duplicate processing
                if (
                    hasattr(event.message, "migrate_to_chat_id")
                    and event.message.migrate_to_chat_id
                ):
                    old_chat_id = event.chat_id
                    new_chat_id = event.message.migrate_to_chat_id

                    force_log(
                        f"Chat migration detected: {old_chat_id} -> {new_chat_id}"
                    )

                    # Migrate the chat_id in the database
                    success = await self.chat_service.migrate_chat_id(
                        old_chat_id, new_chat_id
                    )

                    if success:
                        force_log(
                            f"Successfully migrated chat data from {old_chat_id} to {new_chat_id}"
                        )
                    else:
                        force_log(
                            f"Failed to migrate chat data from {old_chat_id} to {new_chat_id}"
                        )

                    return  # Don't process this message further

                # If not a migration event, process normally
                await self.event_handler.message(event)
            except Exception as e:
                force_log(f"Error in migration_handler: {e}")
                # Don't respond here as it might cause message loops for regular messages
