import logging

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    Application,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from models import ChatService, Chat, ServicePackage, UserService

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

ACTIVATE_COMMAND_CODE = 1001
DEACTIVATE_COMMAND_CODE = 1002
PACKAGE_COMMAND_CODE = 1003


class TelegramAdminBot:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.app: Application | None = None
        self.chat_service = ChatService()
        self.user_service = UserService()
        self.default_question = (
            "Please provide the chat ID by replying to this message."
        )
        logger.info("TelegramAdminBot initialized with token")

    async def validate_user_identifier(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            chat_id = update.message.text.strip()  # type: ignore
            chat = await self._get_chat_with_validation(update, chat_id)
            identifier: str = chat.user.identifier if chat.user else "" # type: ignore
            print(f"Identifier: {identifier}")
            user = await self.user_service.get_user_by_identifier(identifier)
            if not user:
                await update.message.reply_text("User not found.")  # type: ignore
                return ConversationHandler.END

            context.user_data["chat_id_reply"] = identifier  # type: ignore
            return await self.package_button_list(update, context) 
        except ValueError:
            await update.message.reply_text("Invalid identifier.")  # type: ignore
            return ConversationHandler.END

    async def package_button_list(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        if update.message and update.message.reply_to_message:
            if update.message.reply_to_message.message_id == context.user_data.get( # type: ignore
                "expecting_reply_to"
            ):  # type: ignore
                context.user_data["chat_id_reply"] = update.message.text  # type: ignore

        keyboard = [
            [InlineKeyboardButton(ServicePackage.BASIC.value, callback_data="BASIC")],
            [InlineKeyboardButton(ServicePackage.PRO.value, callback_data="PRO")],
            [
                InlineKeyboardButton(
                    ServicePackage.UNLIMITED.value, callback_data="UNLIMITED"
                )
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(  # type: ignore
            "Please choose a subscription package:", reply_markup=reply_markup
        )
        return PACKAGE_COMMAND_CODE

    async def package(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = await update.message.reply_text(self.default_question)  # type: ignore
        context.user_data["expecting_reply_to"] = message.message_id  # type: ignore
        return PACKAGE_COMMAND_CODE

    async def package_button(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        query = update.callback_query
        try:
            if query:
                await query.answer()
                selected_package = query.data
                chat_id: str = context.user_data.get("chat_id_reply") # type: ignore
                chat = self.chat_service.get_chat_by_chat_id(chat_id)
                identifier: str = chat.user.identifier if chat.user else "" # type: ignore
                await self.user_service.update_user_package(identifier, ServicePackage(selected_package))
                if ServicePackage(selected_package) == ServicePackage.UNLIMITED:
                    self.chat_service.update_chat_enable_shift(chat_id, True)
                else:
                    self.chat_service.update_chat_enable_shift(chat_id, False)
                await query.edit_message_text(
                    f"You have successfully subscribed to {selected_package.upper()} package." # type: ignore
                )

                return ConversationHandler.END
            return PACKAGE_COMMAND_CODE
        except Exception as e:
            await query.edit_message_text(# type: ignore
                f"Error updating user package: {e}" 
            )
            return ConversationHandler.END

    async def _get_chat_with_validation(
        self,
        update: Update,
        chat_id: str,
    ) -> Chat | None:
        chat = self.chat_service.get_chat_by_chat_id(chat_id)
        if not chat:
            await update.message.reply_text("Chat is not found.")  # type: ignore
            return None
        return chat

    async def deactivate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(self.default_question)  # type: ignore
        return DEACTIVATE_COMMAND_CODE

    async def activate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(self.default_question)  # type: ignore
        return ACTIVATE_COMMAND_CODE

    async def process_chat_id(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        if not update.message:
            return ConversationHandler.END

        try:
            # Validate not found
            chat_id: str = update.message.text.strip()  # type: ignore
            chat = await self._get_chat_with_validation(update, chat_id)

            # Validate already activated
            if chat.is_active:  # type: ignore
                await update.message.reply_text("Chat has already been activated.")
                return ConversationHandler.END

            self.chat_service.update_chat_status(chat_id, True)
            await update.message.reply_text("Chat has been activated successfully.")

        except ValueError:
            await update.message.reply_text("Invalid chat ID.")

        return ConversationHandler.END

    async def process_deactivate_chat_id(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        if not update.message:
            return ConversationHandler.END

        try:
            chat_id: str = update.message.text.strip()  # type: ignore
            chat = await self._get_chat_with_validation(update, chat_id)

            # Validate already deactivated
            if not chat.is_active:  # type: ignore
                await update.message.reply_text("Chat has already been deactivated.")
                return ConversationHandler.END

            self.chat_service.update_chat_status(chat_id, False)
            await update.message.reply_text("Chat has been deactivated successfully.")

        except ValueError:
            await update.message.reply_text("Invalid chat ID.")

        return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        return ConversationHandler.END

    def setup(self) -> None:
        self.app = ApplicationBuilder().token(self.bot_token).build()

        activate_command_handler = ConversationHandler(
            entry_points=[CommandHandler("activate", self.activate)],
            states={
                ACTIVATE_COMMAND_CODE: [
                    MessageHandler(filters.TEXT & filters.REPLY, self.process_chat_id)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_chat=True,
            per_user=True,
            per_message=False
        )

        deactivate_command_handler = ConversationHandler(
            entry_points=[CommandHandler("deactivate", self.deactivate)],
            states={
                DEACTIVATE_COMMAND_CODE: [
                    MessageHandler(
                        filters.TEXT & filters.REPLY, self.process_deactivate_chat_id
                    )
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_chat=True,
            per_user=True,
            per_message=False
        )

        # Split the package command handler into two separate handlers
        # First handler for text input
        package_text_handler = ConversationHandler(
            entry_points=[CommandHandler("package", self.package)],
            states={
                PACKAGE_COMMAND_CODE: [
                    MessageHandler(filters.TEXT & filters.REPLY, self.validate_user_identifier),
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_chat=True,
            per_user=True,
            per_message=False
        )
        
        # Second handler specifically for button callbacks
        package_button_handler = CallbackQueryHandler(self.package_button)

        self.app.add_handler(activate_command_handler)
        self.app.add_handler(deactivate_command_handler)
        self.app.add_handler(package_text_handler)
        self.app.add_handler(package_button_handler)  # Add the callback handler separately
        logger.info("TelegramAdminBot handlers set up")

    async def start_polling(self) -> None:
        if not self.app:
            self.setup()

        assert self.app is not None
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()  # type: ignore
        logger.info("TelegramAdminBot started polling")
