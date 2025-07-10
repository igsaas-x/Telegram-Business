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

from handlers.event_handler import EventHandler
from models import ChatService, Chat, ServicePackage, UserService

# Get logger (logging configured in main or telegram_bot_service)
logger = logging.getLogger(__name__)

ACTIVATE_COMMAND_CODE = 1001
DEACTIVATE_COMMAND_CODE = 1002
PACKAGE_COMMAND_CODE = 1003
PACKAGE_SELECTION_CODE = 1004
USER_CONFIRMATION_CODE = 1005
ENABLE_SHIFT_COMMAND_CODE = 1006
MENU_COMMAND_CODE = 1007
CALLBACK_QUERY_CODE = 1008


class TelegramAdminBot:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.app: Application | None = None
        self.chat_service = ChatService()
        self.user_service = UserService()
        self.event_handler = EventHandler()
        self.default_question = (
            "Please provide the chat ID by replying to this message."
        )
        logger.info("TelegramAdminBot initialized with token")

    async def validate_user_identifier(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            chat_id = update.message.text.strip()  # type: ignore
            chat = await self._get_chat_with_validation(update, chat_id)
            if not chat:
                return ConversationHandler.END
            
            identifier: str = chat.user.identifier if chat.user else "" # type: ignore
            print(f"Identifier: {identifier}")
            user = await self.user_service.get_user_by_identifier(identifier)
            if not user:
                await update.message.reply_text("User not found.")  # type: ignore
                return ConversationHandler.END

            context.user_data["user_identifier"] = identifier  # type: ignore
            context.user_data["chat_id_input"] = chat_id  # type: ignore
            context.user_data["found_user"] = user  # type: ignore
            return await self.show_user_confirmation(update, context, user) 
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")  # type: ignore
            return ConversationHandler.END


    async def package(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("Use Chat ID", callback_data="use_chat_id")],
            [InlineKeyboardButton("Use Username", callback_data="use_username")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(  # type: ignore
            "How would you like to identify the user?", reply_markup=reply_markup
        )
        return PACKAGE_SELECTION_CODE

    async def package_selection_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        try:
            if query:
                await query.answer()
                selection = query.data
                
                if selection == "use_chat_id":
                    context.user_data["selection_type"] = "chat_id"
                    await query.edit_message_text("Please provide the chat ID by replying to this message.")
                    return PACKAGE_COMMAND_CODE
                elif selection == "use_username":
                    context.user_data["selection_type"] = "username"
                    await query.edit_message_text("Please provide the username by replying to this message.")
                    return PACKAGE_COMMAND_CODE
                    
            return PACKAGE_SELECTION_CODE
        except Exception as e:
            print(f"Error in package_selection_handler: {e}")
            if query:
                await query.edit_message_text(f"Error: {str(e)}")
            return ConversationHandler.END

    async def validate_user_by_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            username = update.message.text.strip()  # type: ignore
            # Remove @ if user included it
            if username.startswith("@"):
                username = username[1:]
            
            user = await self.user_service.get_user_by_username(username)
            if not user:
                await update.message.reply_text("User not found.")  # type: ignore
                return ConversationHandler.END

            context.user_data["user_identifier"] = user.identifier  # type: ignore
            context.user_data["found_user"] = user  # type: ignore
            return await self.show_user_confirmation(update, context, user) 
        except ValueError:
            await update.message.reply_text("Invalid username.")  # type: ignore
            return ConversationHandler.END

    async def show_user_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user) -> int:
        try:
            # Display user information with username
            username = user.username if user.username else "N/A"  # type: ignore
            first_name = user.first_name if user.first_name else "N/A"  # type: ignore
            last_name = user.last_name if user.last_name else "N/A"  # type: ignore
            
            user_info = f"User Found:\n"
            user_info += f"Username: @{username}\n"
            user_info += f"Name: {first_name} {last_name}\n"
            user_info += f"Current Package: {user.package.value}"  # type: ignore
            
            keyboard = [
                [InlineKeyboardButton(f"✅ Confirm (@{username})", callback_data="confirm_user")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_user")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(user_info, reply_markup=reply_markup)  # type: ignore
            return USER_CONFIRMATION_CODE
        except Exception as e:
            print(f"Error in show_user_confirmation: {e}")
            await update.message.reply_text("Error displaying user information.")  # type: ignore
            return ConversationHandler.END

    async def process_package_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        selection_type = context.user_data.get("selection_type")
        
        if selection_type == "chat_id":
            return await self.validate_user_identifier(update, context)
        elif selection_type == "username":
            return await self.validate_user_by_username(update, context)
        else:
            await update.message.reply_text("Invalid selection type.")  # type: ignore
            return ConversationHandler.END

    async def user_confirmation_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        try:
            if query:
                await query.answer()
                action = query.data
                
                if action == "confirm_user":
                    # Show package selection
                    keyboard = [
                        [InlineKeyboardButton(ServicePackage.BASIC.value, callback_data="BASIC")],
                        [InlineKeyboardButton(ServicePackage.PRO.value, callback_data="PRO")],
                        [InlineKeyboardButton(ServicePackage.UNLIMITED.value, callback_data="UNLIMITED")],
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text("Please choose a subscription package:", reply_markup=reply_markup)
                    return PACKAGE_COMMAND_CODE
                    
                elif action == "cancel_user":
                    await query.edit_message_text("Operation cancelled.")
                    return ConversationHandler.END
                    
            return USER_CONFIRMATION_CODE
        except Exception as e:
            print(f"Error in user_confirmation_handler: {e}")
            if query:
                await query.edit_message_text(f"Error: {str(e)}")
            return ConversationHandler.END

    async def package_button(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        query = update.callback_query
        try:
            if query:
                await query.answer()
                selected_package = query.data
                
                # Handle selection buttons
                if selected_package in ["use_chat_id", "use_username"]:
                    return await self.package_selection_handler(update, context)
                
                # Handle user confirmation buttons
                if selected_package in ["confirm_user", "cancel_user"]:
                    return await self.user_confirmation_handler(update, context)
                
                # Handle package selection buttons
                if selected_package in ["BASIC", "PRO", "UNLIMITED"]:
                    user_identifier: str = context.user_data.get("user_identifier") # type: ignore
                    
                    if not user_identifier:
                        await query.edit_message_text("User identifier not found.")
                        return ConversationHandler.END
                    
                    # Update user package with await
                    user = await self.user_service.update_user_package(user_identifier, ServicePackage(selected_package))
                    if not user:
                        await query.edit_message_text("Failed to update user package.")
                        return ConversationHandler.END
                    
                    # Update shift settings based on package change
                    selection_type = context.user_data.get("selection_type")
                    if selection_type == "chat_id":
                        # If using chat_id, update only that specific chat
                        chat_id = context.user_data.get("chat_id_input")
                        if chat_id:
                            if ServicePackage(selected_package) == ServicePackage.UNLIMITED:
                                # When upgrading to unlimited, automatically enable shift
                                await self.chat_service.update_chat_enable_shift(chat_id, True)
                            else:
                                # When downgrading from unlimited, disable shift
                                await self.chat_service.update_chat_enable_shift(chat_id, False)
                    
                    # Get user info for confirmation message
                    found_user = context.user_data.get("found_user")
                    username = found_user.username if found_user and found_user.username else "N/A"  # type: ignore
                    
                    # Confirm to user
                    await query.edit_message_text(
                        f"✅ Successfully updated package to {selected_package} for user @{username}."
                    )
                    return ConversationHandler.END
                
            return PACKAGE_COMMAND_CODE
        except Exception as e:
            print(f"Error in package_button: {e}")
            if query:
                await query.edit_message_text(
                    f"Error updating user package: {str(e)}"
                )
            return ConversationHandler.END

    async def callback_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle callback queries from inline buttons"""
        query = update.callback_query
        
        try:
            # We need to answer the callback query first to stop the loading indicator
            await query.answer()
            
            # Extract the callback data (similar to what Telethon would get)
            callback_data = query.data
            
            # Create a pseudo event for the callback similar to Telethon's events.CallbackQuery
            class PseudoCallbackEvent:
                def __init__(self, callback_query, callback_data):
                    self.chat_id = callback_query.message.chat_id
                    self.data = callback_data
                    self.callback_query = True
                    self.message = callback_query.message
                    
                async def edit(self, text, buttons=None):
                    if buttons:
                        # Convert Telethon buttons to python-telegram-bot InlineKeyboardButton format
                        keyboard = []
                        for row in buttons:
                            keyboard_row = []
                            for button in row:
                                # Extract text and data from button
                                if hasattr(button, "text") and hasattr(button, "data"):
                                    # Convert bytes to string if needed
                                    button_data = button.data
                                    if isinstance(button_data, bytes):
                                        button_data = button_data.decode('utf-8')
                                    
                                    keyboard_row.append(
                                        InlineKeyboardButton(button.text, callback_data=button_data)
                                    )
                            if keyboard_row:
                                keyboard.append(keyboard_row)
                        
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await query.edit_message_text(text, reply_markup=reply_markup)
                    else:
                        await query.edit_message_text(text)
                        
                async def respond(self, text, buttons=None):
                    """For cases where a new message needs to be sent instead of editing"""
                    if buttons:
                        # Convert Telethon buttons to python-telegram-bot format
                        keyboard = []
                        for row in buttons:
                            keyboard_row = []
                            for button in row:
                                if hasattr(button, "text") and hasattr(button, "data"):
                                    # Convert bytes to string if needed
                                    button_data = button.data
                                    if isinstance(button_data, bytes):
                                        button_data = button_data.decode('utf-8')
                                    
                                    keyboard_row.append(
                                        InlineKeyboardButton(button.text, callback_data=button_data)
                                    )
                            if keyboard_row:
                                keyboard.append(keyboard_row)
                        
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await query.message.reply_text(text, reply_markup=reply_markup)
                    else:
                        await query.message.reply_text(text)
            
            # Create pseudo event
            pseudo_event = PseudoCallbackEvent(query, callback_data)
            
            # Call the event_handler's callback method
            await self.event_handler.callback(pseudo_event)
            
            return CALLBACK_QUERY_CODE
            
        except Exception as e:
            logger.error(f"Error in callback_query_handler: {e}", exc_info=True)
            await query.message.reply_text(f"Error processing button action: {str(e)}")
            return ConversationHandler.END

    async def _get_chat_with_validation(
        self,
        update: Update,
        chat_id: str,
    ) -> Chat | None:
        chat = await self.chat_service.get_chat_by_chat_id(chat_id)
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

    async def enable_shift(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(self.default_question)  # type: ignore
        return ENABLE_SHIFT_COMMAND_CODE

    async def process_chat_id(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        if not update.message:
            return ConversationHandler.END

        try:
            # Validate not found
            chat_id: str = update.message.text.strip()  # type: ignore
            chat = await self._get_chat_with_validation(update, chat_id)
            if not chat:
                return ConversationHandler.END

            # Validate already activated
            if chat.is_active:  # type: ignore
                await update.message.reply_text("Chat has already been activated.")
                return ConversationHandler.END

            await self.chat_service.update_chat_status(chat_id, True)
            await update.message.reply_text("Chat has been activated successfully.")

        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")

        return ConversationHandler.END

    async def process_deactivate_chat_id(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        if not update.message:
            return ConversationHandler.END

        try:
            chat_id: str = update.message.text.strip()  # type: ignore
            chat = await self._get_chat_with_validation(update, chat_id)
            if not chat:
                return ConversationHandler.END

            # Validate already deactivated
            if not chat.is_active:  # type: ignore
                await update.message.reply_text("Chat has already been deactivated.")
                return ConversationHandler.END

            await self.chat_service.update_chat_status(chat_id, False)
            await update.message.reply_text("Chat has been deactivated successfully.")

        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")

        return ConversationHandler.END

    async def process_enable_shift_chat_id(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        if not update.message:
            return ConversationHandler.END

        try:
            chat_id: str = update.message.text.strip()  # type: ignore
            chat = await self._get_chat_with_validation(update, chat_id)
            if not chat:
                return ConversationHandler.END

            # Check if chat has a user
            if not chat.user:  # type: ignore
                await update.message.reply_text("Chat does not have an associated user.")
                return ConversationHandler.END

            # Check if user has unlimited package
            if chat.user.package != ServicePackage.UNLIMITED:  # type: ignore
                await update.message.reply_text(
                    f"User must have UNLIMITED package to enable shift. Current package: {chat.user.package.value}"  # type: ignore
                )
                return ConversationHandler.END

            # Check if shift is already enabled
            if chat.enable_shift:  # type: ignore
                await update.message.reply_text("Shift is already enabled for this chat.")
                return ConversationHandler.END

            # Enable shift for the chat
            await self.chat_service.update_chat_enable_shift(chat_id, True)
            await update.message.reply_text("Shift has been enabled successfully for this chat.")

        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")

        return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        return ConversationHandler.END

    async def menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(self.default_question)  # type: ignore
        return MENU_COMMAND_CODE
        
    async def process_menu_chat_id(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        if not update.message:
            return ConversationHandler.END

        try:
            chat_id: str = update.message.text.strip()  # type: ignore
            chat = await self._get_chat_with_validation(update, chat_id)
            if not chat:
                return ConversationHandler.END
                
            # Create a pseudo-event object with the chat_id for the event_handler
            class PseudoEvent:
                def __init__(self, chat_id, message):
                    self.chat_id = int(chat_id)
                    self.message = message
                    self.callback_query = None  # Not a callback
                    
                async def get_sender(self):
                    # Return None to skip auto-registration logic
                    return None
                    
                async def respond(self, text, buttons=None):
                    if buttons:
                        # Convert Telethon buttons to python-telegram-bot InlineKeyboardButton format
                        keyboard = []
                        for row in buttons:
                            keyboard_row = []
                            for button in row:
                                # Extract text and data from button
                                if hasattr(button, "text") and hasattr(button, "data"):
                                    # Convert bytes to string if needed
                                    button_data = button.data
                                    if isinstance(button_data, bytes):
                                        button_data = button_data.decode('utf-8')
                                    
                                    keyboard_row.append(
                                        InlineKeyboardButton(button.text, callback_data=button_data)
                                    )
                            if keyboard_row:
                                keyboard.append(keyboard_row)
                        
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await update.message.reply_text(text, reply_markup=reply_markup)  # type: ignore
                    else:
                        await update.message.reply_text(text)  # type: ignore
                
                async def edit(self, text, buttons=None):
                    # Same as respond for admin bot since we're sending new messages
                    await self.respond(text, buttons)
            
            # Create pseudo-event with the provided chat_id
            pseudo_event = PseudoEvent(int(chat_id), update.message)
            
            # Call the event_handler's menu method with our pseudo-event
            await self.event_handler.menu(pseudo_event)

        except Exception as e:
            await update.message.reply_text(f"Error processing menu: {str(e)}")  # type: ignore
            logger.error(f"Error in process_menu_chat_id: {e}", exc_info=True)

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

        # Package command handler with multiple states
        # Note: per_message=False warning is expected when mixing CallbackQueryHandler with other handler types
        package_handler = ConversationHandler(
            entry_points=[CommandHandler("package", self.package)],
            states={
                PACKAGE_SELECTION_CODE: [
                    CallbackQueryHandler(self.package_button)
                ],
                PACKAGE_COMMAND_CODE: [
                    MessageHandler(filters.TEXT & filters.REPLY, self.process_package_input),
                    CallbackQueryHandler(self.package_button)
                ],
                USER_CONFIRMATION_CODE: [
                    CallbackQueryHandler(self.package_button)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_chat=True,
            per_user=True,
            per_message=False
        )

        enable_shift_handler = ConversationHandler(
            entry_points=[CommandHandler("enable_shift", self.enable_shift)],
            states={
                ENABLE_SHIFT_COMMAND_CODE: [
                    MessageHandler(filters.TEXT & filters.REPLY, self.process_enable_shift_chat_id)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_chat=True,
            per_user=True,
            per_message=False
        )

        menu_handler = ConversationHandler(
            entry_points=[CommandHandler("menu", self.menu)],
            states={
                MENU_COMMAND_CODE: [
                    MessageHandler(filters.TEXT & filters.REPLY, self.process_menu_chat_id)
                ],
                CALLBACK_QUERY_CODE: [
                    CallbackQueryHandler(self.callback_query_handler)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_chat=True,
            per_user=True,
            per_message=False
        )

        self.app.add_handler(activate_command_handler)
        self.app.add_handler(deactivate_command_handler)
        self.app.add_handler(package_handler)
        self.app.add_handler(enable_shift_handler)
        self.app.add_handler(menu_handler)
        
        # Add a global callback query handler outside the conversation handlers
        self.app.add_handler(CallbackQueryHandler(self.callback_query_handler))
        logger.info("TelegramAdminBot handlers set up")

    async def start_polling(self) -> None:
        if not self.app:
            self.setup()

        assert self.app is not None
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()  # type: ignore
        logger.info("TelegramAdminBot started polling")
