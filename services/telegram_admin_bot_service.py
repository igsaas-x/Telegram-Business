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

from handlers.bot_command_handler import EventHandler
from helper.logger_utils import force_log
from services.shift_permission_service import ShiftPermissionService
from .handlers import ChatSearchHandler, MenuHandler, PackageHandler

# Conversation state codes
PACKAGE_COMMAND_CODE = 1003
PACKAGE_SELECTION_CODE = 1004
USER_CONFIRMATION_CODE = 1005
ENABLE_SHIFT_COMMAND_CODE = 1006
MENU_COMMAND_CODE = 1007
CALLBACK_QUERY_CODE = 1008
GET_USERNAME_COMMAND_CODE = 1009
CHAT_SELECTION_CODE = 1010
ACTIVATE_SELECTION_CODE = 1011
DEACTIVATE_SELECTION_CODE = 1012
ENABLE_SHIFT_SELECTION_CODE = 1013
PACKAGE_START_DATE_CODE = 1014
PACKAGE_END_DATE_CODE = 1015
AMOUNT_PAID_CODE = 1016
NOTE_CONFIRMATION_CODE = 1017
NOTE_INPUT_CODE = 1018
QUERY_PACKAGE_SELECTION_CODE = 1019
QUERY_PACKAGE_COMMAND_CODE = 1020
QUERY_PACKAGE_CHAT_SELECTION_CODE = 1021
SHIFT_PERMISSION_SELECTION_CODE = 1022
SHIFT_PERMISSION_COMMAND_CODE = 1023
SHIFT_PERMISSION_CHAT_SELECTION_CODE = 1024
SHIFT_PERMISSION_USERNAME_CODE = 1025


class TelegramAdminBot:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.app: Application | None = None
        self.event_handler = EventHandler()
        self.default_question = (
            "Please provide the chat ID by replying to this message."
        )
        self.telethon_client = None
        
        # Initialize handlers
        self.chat_search_handler = ChatSearchHandler()
        self.menu_handler = MenuHandler()
        self.package_handler = PackageHandler()
        self.shift_permission_service = ShiftPermissionService()
        
        force_log("TelegramAdminBot initialized with token", "TelegramAdminBot")

    @staticmethod
    async def package(update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["command_type"] = "package"  # type: ignore
        keyboard = [
            [InlineKeyboardButton("Use Chat ID", callback_data="use_chat_id")],
            [InlineKeyboardButton("Use Group Name", callback_data="use_group_name")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(  # type: ignore
            "How would you like to identify the user?", reply_markup=reply_markup
        )
        return PACKAGE_SELECTION_CODE

    @staticmethod
    async def query_package(update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["command_type"] = "query_package"  # type: ignore
        keyboard = [
            [InlineKeyboardButton("Use Chat ID", callback_data="use_chat_id")],
            [InlineKeyboardButton("Use Group Name", callback_data="use_group_name")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(  # type: ignore
            "How would you like to identify the group to query?", reply_markup=reply_markup
        )
        return QUERY_PACKAGE_SELECTION_CODE

    @staticmethod
    async def package_selection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        try:
            if query:
                await query.answer()
                selection = query.data

                if selection == "use_chat_id":
                    context.user_data["selection_type"] = "chat_id"
                    await query.edit_message_text(
                        "Please provide the chat ID by replying to this message."
                    )
                    return PACKAGE_COMMAND_CODE
                elif selection == "use_group_name":
                    context.user_data["selection_type"] = "group_name"
                    await query.edit_message_text(
                        "Please provide the group name to search. You can enter partial group name (up to 5 results will be shown)."
                    )
                    return PACKAGE_COMMAND_CODE

            return PACKAGE_SELECTION_CODE
        except Exception as e:
            force_log(f"Error in package_selection_handler: {e}", "TelegramAdminBot")
            if query:
                await query.edit_message_text(f"Error: {str(e)}")
            return ConversationHandler.END

    @staticmethod
    async def enable_shift(update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["command_type"] = "enable_shift"  # type: ignore
        keyboard = [
            [InlineKeyboardButton("Use Chat ID", callback_data="use_chat_id")],
            [InlineKeyboardButton("Use Group Name", callback_data="use_group_name")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(  # type: ignore
            "How would you like to find the chat to enable shift?", reply_markup=reply_markup
        )
        return ENABLE_SHIFT_SELECTION_CODE

    async def menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(self.default_question)  # type: ignore
        return MENU_COMMAND_CODE

    async def process_menu_chat_id(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        if not update.message:
            return ConversationHandler.END

        try:
            chat_id: int = int(update.message.text.strip())  # type: ignore
            chat = await self.chat_search_handler._get_chat_with_validation(update, chat_id)
            if not chat:
                return ConversationHandler.END

            # Store the chat_id in context for use in callback queries
            context.user_data["admin_chat_id"] = chat_id

            # Create buttons for the menu
            keyboard = [
                [InlineKeyboardButton("ប្រចាំថ្ងៃ", callback_data="daily_summary")],
                [InlineKeyboardButton("ប្រចាំសប្តាហ៍", callback_data="weekly_summary")],
                [InlineKeyboardButton("ប្រចាំខែ", callback_data="monthly_summary")],
                [InlineKeyboardButton("បិទ", callback_data="close_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                "ជ្រើសរើសរបាយការណ៍ប្រចាំ:", reply_markup=reply_markup
            )

        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")  # type: ignore
            force_log(f"Error in process_menu_chat_id: {e}", "TelegramAdminBot")

        return CALLBACK_QUERY_CODE

    async def callback_query_handler(self, update: Update) -> int:
        """Handle callback queries from inline buttons"""
        query = update.callback_query

        try:
            # We need to answer the callback query first to stop the loading indicator
            await query.answer()

            # Extract the callback data (similar to what Telethon would get)
            callback_data = query.data

            # Create a pseudo-event for the callback similar to Telethon's events.CallbackQuery
            class PseudoCallbackEvent:
                def __init__(self, callback_query, callback_data):
                    self.chat_id = callback_query.message.chat_id
                    self.data = (
                        callback_data.encode("utf-8")
                        if isinstance(callback_data, str)
                        else callback_data
                    )
                    self.callback_query = True
                    self.message = callback_query.message

                @staticmethod
                async def edit(text, buttons=None):
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
                                        button_data = button_data.decode("utf-8")
                                    elif not isinstance(button_data, str):
                                        button_data = str(button_data)

                                    keyboard_row.append(
                                        InlineKeyboardButton(
                                            button.text, callback_data=button_data
                                        )
                                    )
                            if keyboard_row:
                                keyboard.append(keyboard_row)

                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await query.edit_message_text(text, reply_markup=reply_markup)
                    else:
                        await query.edit_message_text(text)

                @staticmethod
                async def respond(text, buttons=None):
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
                                        button_data = button_data.decode("utf-8")
                                    elif not isinstance(button_data, str):
                                        button_data = str(button_data)

                                    keyboard_row.append(
                                        InlineKeyboardButton(
                                            button.text, callback_data=button_data
                                        )
                                    )
                            if keyboard_row:
                                keyboard.append(keyboard_row)

                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await query.edit_message_text(text, reply_markup=reply_markup)
                    else:
                        await query.edit_message_text(text)

            # Create pseudo-event
            pseudo_event = PseudoCallbackEvent(query, callback_data)

            # Call the event_handler's callback method
            await self.event_handler.callback(pseudo_event)

            return CALLBACK_QUERY_CODE

        except Exception as e:
            force_log(f"Error in callback_query_handler: {e}", "TelegramAdminBot")
            try:
                await query.edit_message_text(f"Error processing button action: {str(e)}")
            except Exception:
                pass
            return ConversationHandler.END

    @staticmethod
    async def shift_permission(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /shift_permission command"""
        context.user_data["command_type"] = "shift_permission"
        keyboard = [
            [InlineKeyboardButton("Use Chat ID", callback_data="use_chat_id")],
            [InlineKeyboardButton("Use Group Name", callback_data="use_group_name")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "How would you like to identify the chat to manage shift permissions?", 
            reply_markup=reply_markup
        )
        return SHIFT_PERMISSION_SELECTION_CODE

    async def shift_permission_selection_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle shift permission selection"""
        query = update.callback_query
        try:
            if query:
                await query.answer()
                selection = query.data

                if selection == "use_chat_id":
                    context.user_data["selection_type"] = "chat_id"
                    await query.edit_message_text(
                        "Please provide the chat ID by replying to this message."
                    )
                    return SHIFT_PERMISSION_COMMAND_CODE
                elif selection == "use_group_name":
                    context.user_data["selection_type"] = "group_name"
                    await query.edit_message_text(
                        "Please provide the group name to search. You can enter partial group name (up to 5 results will be shown)."
                    )
                    return SHIFT_PERMISSION_COMMAND_CODE

            return SHIFT_PERMISSION_SELECTION_CODE
        except Exception as e:
            force_log(f"Error in shift_permission_selection_handler: {e}", "TelegramAdminBot")
            if query:
                await query.edit_message_text(f"Error: {str(e)}")
            return ConversationHandler.END

    async def shift_permission_chat_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle chat selection for shift permissions"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Extract chat ID from callback data
            chat_id = int(query.data.replace("chat_", ""))
            context.user_data["selected_chat_id"] = chat_id
            
            # Get current allowed users
            allowed_users = await self.shift_permission_service.get_allowed_users(chat_id)
            
            if allowed_users:
                users_text = "\n".join([f"• {user}" for user in allowed_users])
                current_users = f"\n\n**Current allowed users:**\n{users_text}"
            else:
                current_users = "\n\n**Current allowed users:** None"
            
            keyboard = [
                [InlineKeyboardButton("Add User", callback_data="add_user")],
                [InlineKeyboardButton("Remove User", callback_data="remove_user")],
                [InlineKeyboardButton("List Users", callback_data="list_users")],
                [InlineKeyboardButton("Clear All", callback_data="clear_all")],
                [InlineKeyboardButton("Cancel", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"**Shift Permission Management**\nSelected chat ID: {chat_id}{current_users}\n\nWhat would you like to do?",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            
            return SHIFT_PERMISSION_USERNAME_CODE
            
        except Exception as e:
            force_log(f"Error in shift_permission_chat_selection: {e}", "TelegramAdminBot")
            await query.edit_message_text(f"Error: {str(e)}")
            return ConversationHandler.END

    async def shift_permission_action_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle shift permission actions (add/remove/list/clear)"""
        query = update.callback_query
        await query.answer()
        
        try:
            action = query.data
            chat_id = context.user_data.get("selected_chat_id")
            
            if not chat_id:
                await query.edit_message_text("Error: No chat selected")
                return ConversationHandler.END
            
            if action == "add_user":
                context.user_data["permission_action"] = "add"
                await query.edit_message_text(
                    "Please reply with the username to add (with or without @ symbol):"
                )
                return SHIFT_PERMISSION_USERNAME_CODE
                
            elif action == "remove_user":
                context.user_data["permission_action"] = "remove"
                await query.edit_message_text(
                    "Please reply with the username to remove (with or without @ symbol):"
                )
                return SHIFT_PERMISSION_USERNAME_CODE
                
            elif action == "list_users":
                allowed_users = await self.shift_permission_service.get_allowed_users(chat_id)
                if allowed_users:
                    users_text = "\n".join([f"• {user}" for user in allowed_users])
                    message = f"**Allowed users for chat {chat_id}:**\n{users_text}"
                else:
                    message = f"**No users allowed for chat {chat_id}**"
                
                await query.edit_message_text(message, parse_mode="Markdown")
                return ConversationHandler.END
                
            elif action == "clear_all":
                count = await self.shift_permission_service.clear_all_permissions(chat_id)
                await query.edit_message_text(
                    f"✅ Cleared {count} shift permissions for chat {chat_id}"
                )
                return ConversationHandler.END
                
            elif action == "cancel":
                await query.edit_message_text("Operation cancelled")
                return ConversationHandler.END
                
        except Exception as e:
            force_log(f"Error in shift_permission_action_handler: {e}", "TelegramAdminBot")
            await query.edit_message_text(f"Error: {str(e)}")
            return ConversationHandler.END

    async def process_shift_permission_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Process username input for shift permissions"""
        if not update.message or not update.message.text:
            return ConversationHandler.END
        
        try:
            username = update.message.text.strip()
            chat_id = context.user_data.get("selected_chat_id")
            action = context.user_data.get("permission_action")
            
            if not chat_id or not action:
                await update.message.reply_text("Error: Missing chat or action information")
                return ConversationHandler.END
            
            if action == "add":
                success = await self.shift_permission_service.add_allowed_user(chat_id, username)
                if success:
                    await update.message.reply_text(
                        f"✅ Successfully added @{username.lstrip('@')} to shift close permissions for chat {chat_id}"
                    )
                else:
                    await update.message.reply_text(
                        f"⚠️ User @{username.lstrip('@')} already has permissions or an error occurred"
                    )
                    
            elif action == "remove":
                success = await self.shift_permission_service.remove_allowed_user(chat_id, username)
                if success:
                    await update.message.reply_text(
                        f"✅ Successfully removed @{username.lstrip('@')} from shift close permissions for chat {chat_id}"
                    )
                else:
                    await update.message.reply_text(
                        f"⚠️ User @{username.lstrip('@')} doesn't have permissions or an error occurred"
                    )
            
            return ConversationHandler.END
            
        except Exception as e:
            force_log(f"Error in process_shift_permission_username: {e}", "TelegramAdminBot")
            await update.message.reply_text(f"Error: {str(e)}")
            return ConversationHandler.END

    @staticmethod
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text("Session has been cancelled")
        return ConversationHandler.END


    def setup(self) -> None:
        self.app = ApplicationBuilder().token(self.bot_token).build()

        # Package command handler with multiple states
        package_handler = ConversationHandler(
            entry_points=[CommandHandler("package", self.package)],
            states={
                PACKAGE_SELECTION_CODE: [CallbackQueryHandler(self.chat_search_handler.shared_selection_handler)],
                PACKAGE_COMMAND_CODE: [
                    MessageHandler(
                        filters.TEXT & filters.REPLY, self.chat_search_handler.shared_process_input
                    ),
                    CallbackQueryHandler(self.package_handler.package_button),
                ],
                USER_CONFIRMATION_CODE: [CallbackQueryHandler(self.package_handler.package_button)],
                CHAT_SELECTION_CODE: [CallbackQueryHandler(self.chat_search_handler.handle_chat_selection)],
                PACKAGE_START_DATE_CODE: [
                    MessageHandler(filters.TEXT & filters.REPLY, self.package_handler.process_package_start_date),
                    CallbackQueryHandler(self.package_handler.package_button)
                ],
                PACKAGE_END_DATE_CODE: [
                    MessageHandler(filters.TEXT & filters.REPLY, self.package_handler.process_package_end_date),
                    CallbackQueryHandler(self.package_handler.package_button)
                ],
                AMOUNT_PAID_CODE: [MessageHandler(filters.TEXT & filters.REPLY, self.package_handler.process_amount_paid)],
                NOTE_CONFIRMATION_CODE: [CallbackQueryHandler(self.package_handler.handle_note_confirmation)],
                NOTE_INPUT_CODE: [MessageHandler(filters.TEXT & filters.REPLY, self.package_handler.process_note_input)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_chat=True,
            per_user=True,
            per_message=False,
        )

        enable_shift_handler = ConversationHandler(
            entry_points=[CommandHandler("enable_shift", self.enable_shift)],
            states={
                ENABLE_SHIFT_SELECTION_CODE: [CallbackQueryHandler(self.chat_search_handler.shared_selection_handler)],
                ENABLE_SHIFT_COMMAND_CODE: [
                    MessageHandler(filters.TEXT & filters.REPLY, self.chat_search_handler.shared_process_input),
                    CallbackQueryHandler(self.chat_search_handler.shared_selection_handler),
                ],
                CHAT_SELECTION_CODE: [CallbackQueryHandler(self.chat_search_handler.handle_chat_selection)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_chat=True,
            per_user=True,
            per_message=False,
        )

        menu_handler = ConversationHandler(
            entry_points=[CommandHandler("menu", self.menu)],
            states={
                MENU_COMMAND_CODE: [
                    MessageHandler(
                        filters.TEXT & filters.REPLY, self.process_menu_chat_id
                    )
                ],
                CALLBACK_QUERY_CODE: [
                    CallbackQueryHandler(self.menu_handler.menu_callback_query_handler)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_chat=True,
            per_user=True,
            per_message=False,
        )

        query_package_handler = ConversationHandler(
            entry_points=[CommandHandler("query_package", self.query_package)],
            states={
                QUERY_PACKAGE_SELECTION_CODE: [CallbackQueryHandler(self.chat_search_handler.shared_selection_handler)],
                QUERY_PACKAGE_COMMAND_CODE: [
                    MessageHandler(filters.TEXT & filters.REPLY, self.chat_search_handler.shared_process_input),
                    CallbackQueryHandler(self.chat_search_handler.shared_selection_handler),
                ],
                QUERY_PACKAGE_CHAT_SELECTION_CODE: [CallbackQueryHandler(self.chat_search_handler.handle_chat_selection)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_chat=True,
            per_user=True,
            per_message=False,
        )

        shift_permission_handler = ConversationHandler(
            entry_points=[CommandHandler("shift_permission", self.shift_permission)],
            states={
                SHIFT_PERMISSION_SELECTION_CODE: [CallbackQueryHandler(self.shift_permission_selection_handler)],
                SHIFT_PERMISSION_COMMAND_CODE: [
                    MessageHandler(filters.TEXT & filters.REPLY, self.chat_search_handler.shared_process_input),
                    CallbackQueryHandler(self.shift_permission_selection_handler),
                ],
                SHIFT_PERMISSION_CHAT_SELECTION_CODE: [CallbackQueryHandler(self.shift_permission_chat_selection)],
                SHIFT_PERMISSION_USERNAME_CODE: [
                    MessageHandler(filters.TEXT & filters.REPLY, self.process_shift_permission_username),
                    CallbackQueryHandler(self.shift_permission_action_handler),
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_chat=True,
            per_user=True,
            per_message=False,
        )

        self.app.add_handler(package_handler)
        self.app.add_handler(enable_shift_handler)
        self.app.add_handler(menu_handler)
        self.app.add_handler(query_package_handler)
        self.app.add_handler(shift_permission_handler)

        force_log("TelegramAdminBot handlers set up", "TelegramAdminBot")

    async def start_polling(self) -> None:
        if not self.app:
            self.setup()

        assert self.app is not None
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()  # type: ignore
        force_log("TelegramAdminBot started polling", "TelegramAdminBot")

    async def send_message(self, chat_id: int, message: str) -> bool:
        """
        Send a message to a specific chat using the admin bot
        
        Args:
            chat_id: The chat ID to send the message to
            message: The message text to send
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        try:
            if self.app and self.app.bot:
                await self.app.bot.send_message(chat_id=chat_id, text=message)
                force_log(f"Admin bot sent message to chat {chat_id}: {message[:50]}...", "TelegramAdminBot")
                return True
            else:
                force_log("Admin bot application not initialized, cannot send message", "TelegramAdminBot")
                return False
        except Exception as e:
            force_log(f"Failed to send message via admin bot to chat {chat_id}: {str(e)}", "TelegramAdminBot")
            return False