import asyncio

from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    Application,
    filters,
)

from handlers import EventHandler
from helper.logger_utils import force_log
from models import User
from services import UserService, ChatService


class TelegramBotService:
    def __init__(self):
        self.bot: Bot = None  # type: ignore
        self.application: Application = None  # type: ignore
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
                await self.bot.send_message(chat_id=chat_id, text=message)
                force_log(f"Message sent to chat {chat_id}: {message[:50]}...")
            else:
                force_log("Bot is not initialized, cannot send message")
        except Exception as e:
            force_log(f"Failed to send message to chat {chat_id}: {str(e)}")

    async def start(self, bot_token: str):
        self.application = ApplicationBuilder().token(bot_token).build()
        self.bot = self.application.bot
        
        self._register_handlers()

        try:
            force_log("Bot is running...")
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            # Keep running until cancelled
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            force_log("Bot stopped by user")
        except Exception as e:
            force_log(f"Bot crashed with error: {e}")
            raise
        finally:
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()

    def _register_handlers(self):
        async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                # Check if this is a private chat
                if update.effective_chat.type == 'private':
                    await update.message.reply_text("❌ This bot only works in groups. Please add this bot to a group to use it.")
                    return
                
                await self.event_handler.menu(update)
            except Exception as e:
                force_log(f"Error in menu_handler: {e}")
                await update.message.reply_text("An error occurred. Please try again.")

        async def register_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                chat_id = update.effective_chat.id
                force_log(f"Registration attempt from chat {chat_id}")
                
                # Check if this is a private chat
                if update.effective_chat.type == 'private':
                    await update.message.reply_text("❌ This bot only works in groups. Please add this bot to a group to use it.")
                    return
                
                # Always insert user if not exists, regardless of chat_id existence
                sender = update.effective_user

                registered_user: User | None = None
                # Check if sender exists
                if sender and sender.id:
                    registered_user = await self.user_service.create_user(sender)
                    force_log(
                        f"Registration request from user {sender.id} in chat {chat_id}"
                    )

                # Check if chat_id already exists
                existing_chat = await self.chat_service.get_chat_by_chat_id(chat_id)
                if existing_chat:
                    # Update the existing chat with the current user_id
                    if registered_user and existing_chat.user_id != registered_user.id:
                        force_log(
                            f"Updated existing chat {chat_id} with new user {registered_user.id}"
                        )
                        await self.chat_service.update_chat_user_id(
                            chat_id, registered_user.id
                        )
                        await update.message.reply_text(
                            f"Chat ID {chat_id} is already registered. Updated with current user."
                        )
                    else:
                        force_log(
                            f"Chat {chat_id} already registered with same user"
                        )
                        await update.message.reply_text(
                            f"Chat ID {chat_id} is already registered with the same user."
                        )
                    return

                force_log(f"Proceeding with new registration for chat {chat_id}")
                await self.event_handler.register(update, registered_user)
            except Exception as e:
                print(f"Error on registration {e}")
                force_log(f"Error in register_handler: {e}")
                await update.message.reply_text(
                    "An error occurred during registration. Please try again."
                )

        async def contact_us_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                message = "សូមទាក់ទងយើងខ្ញុំតាមរយៈ Telegram៖ https://t.me/HK_688"
                await update.message.reply_text(message)
            except Exception as e:
                force_log(f"Error in contact_us_handler: {e}")
                await update.message.reply_text("An error occurred. Please try again.")

        async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                await self.event_handler.callback(update)
            except Exception as e:
                print(f"Error in callback_handler: {e}")
                force_log(f"Error in callback_handler: {e}")
                await update.callback_query.answer("An error occurred. Please try again.")

        async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                # Handle chat migration
                if update.message.migrate_to_chat_id:
                    old_chat_id = update.effective_chat.id
                    new_chat_id = update.message.migrate_to_chat_id

                    force_log(f"Chat migration detected: {old_chat_id} -> {new_chat_id}")

                    # Migrate the chat_id in the database
                    success = await self.chat_service.migrate_chat_id(old_chat_id, new_chat_id)

                    if success:
                        force_log(f"Successfully migrated chat data from {old_chat_id} to {new_chat_id}")
                    else:
                        force_log(f"Failed to migrate chat data from {old_chat_id} to {new_chat_id}")

                    return  # Don't process this message further

                # If not a migration event, process normally
                await self.event_handler.message(update)
            except Exception as e:
                force_log(f"Error in message_handler: {e}")
                # Don't respond here as it might cause message loops for regular messages

        # Add handlers to application
        self.application.add_handler(CommandHandler("menu", menu_handler))
        self.application.add_handler(CommandHandler("register", register_handler))
        self.application.add_handler(CommandHandler("contact_us", contact_us_handler))
        self.application.add_handler(CallbackQueryHandler(callback_handler))
        self.application.add_handler(MessageHandler(filters.ALL, message_handler))
