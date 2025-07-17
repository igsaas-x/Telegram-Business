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

from handlers.bot_command_handler import EventHandler
from services import ChatService, UserService
from .group_package_service import GroupPackageService
from common.enums import ServicePackage
from models import Chat

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
        self.group_package_service = GroupPackageService()
        self.event_handler = EventHandler()
        self.default_question = (
            "Please provide the chat ID by replying to this message."
        )
        logger.info("TelegramAdminBot initialized with token")

    async def validate_user_identifier(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        try:
            chat_id = update.message.text.strip()  # type: ignore
            chat = await self._get_chat_with_validation(update, chat_id)
            if not chat:
                return ConversationHandler.END

            identifier: str = chat.user.identifier if chat.user else ""  # type: ignore
            logger.debug(f"Identifier: {identifier}")
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

    async def package_selection_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
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
                elif selection == "use_username":
                    context.user_data["selection_type"] = "username"
                    await query.edit_message_text(
                        "Please provide the username by replying to this message."
                    )
                    return PACKAGE_COMMAND_CODE

            return PACKAGE_SELECTION_CODE
        except Exception as e:
            logger.error(f"Error in package_selection_handler: {e}")
            if query:
                await query.edit_message_text(f"Error: {str(e)}")
            return ConversationHandler.END

    async def validate_user_by_username(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
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

    async def show_user_confirmation(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, user
    ) -> int:
        try:
            # Display user information with username
            username = user.username if user.username else "N/A"  # type: ignore
            first_name = user.first_name if user.first_name else "N/A"  # type: ignore
            last_name = user.last_name if user.last_name else "N/A"  # type: ignore

            user_info = f"User Found:\n"
            user_info += f"Username: @{username}\n"
            user_info += f"Name: {first_name} {last_name}\n"

            # Get package info from chat if available
            chat_id = context.user_data.get("chat_id_input")
            if chat_id:
                group_package = await self.group_package_service.get_package_by_chat_id(
                    chat_id
                )
                if group_package:
                    user_info += f"Current Package: {group_package.package.value}"
                else:
                    user_info += f"Current Package: No package assigned"
            else:
                user_info += f"Current Package: N/A (no chat specified)"

            keyboard = [
                [
                    InlineKeyboardButton(
                        f"✅ Confirm (@{username})", callback_data="confirm_user"
                    )
                ],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_user")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(user_info, reply_markup=reply_markup)  # type: ignore
            return USER_CONFIRMATION_CODE
        except Exception as e:
            logger.error(f"Error in show_user_confirmation: {e}")
            await update.message.reply_text("Error displaying user information.")  # type: ignore
            return ConversationHandler.END

    async def process_package_input(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        selection_type = context.user_data.get("selection_type")

        if selection_type == "chat_id":
            return await self.validate_user_identifier(update, context)
        elif selection_type == "username":
            return await self.validate_user_by_username(update, context)
        else:
            await update.message.reply_text("Invalid selection type.")  # type: ignore
            return ConversationHandler.END

    async def user_confirmation_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        query = update.callback_query
        try:
            if query:
                await query.answer()
                action = query.data

                if action == "confirm_user":
                    # Show package selection
                    keyboard = [
                        [
                            InlineKeyboardButton(
                                ServicePackage.TRIAL.value, callback_data="TRIAL"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                ServicePackage.BASIC.value, callback_data="BASIC"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                ServicePackage.UNLIMITED.value,
                                callback_data="UNLIMITED",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                ServicePackage.BUSINESS.value, callback_data="BUSINESS"
                            )
                        ],
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text(
                        "Please choose a subscription package:",
                        reply_markup=reply_markup,
                    )
                    return PACKAGE_COMMAND_CODE

                elif action == "cancel_user":
                    await query.edit_message_text("Operation cancelled.")
                    return ConversationHandler.END

            return USER_CONFIRMATION_CODE
        except Exception as e:
            logger.error(f"Error in user_confirmation_handler: {e}")
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
                if selected_package in ["TRIAL", "BASIC", "UNLIMITED", "BUSINESS"]:
                    chat_id = context.user_data.get("chat_id_input")

                    if not chat_id:
                        await query.edit_message_text("Chat ID not found.")
                        return ConversationHandler.END

                    # Update group package
                    group_package = (
                        await self.group_package_service.get_or_create_group_package(
                            chat_id
                        )
                    )
                    updated_package = await self.group_package_service.update_package(
                        chat_id, ServicePackage(selected_package)
                    )

                    if not updated_package:
                        await query.edit_message_text("Failed to update group package.")
                        return ConversationHandler.END

                    # Update shift settings based on package change
                    if ServicePackage(selected_package) == ServicePackage.BUSINESS:
                        # When upgrading to business, automatically enable shift
                        await self.chat_service.update_chat_enable_shift(chat_id, True)
                    elif ServicePackage(selected_package) == ServicePackage.TRIAL:
                        # When downgrading to trial, disable shift
                        await self.chat_service.update_chat_enable_shift(chat_id, False)

                    # Get user info for confirmation message
                    found_user = context.user_data.get("found_user")
                    username = found_user.username if found_user and found_user.username else "N/A"  # type: ignore

                    # Confirm to user
                    await query.edit_message_text(
                        f"✅ Successfully updated package to {selected_package} for chat {chat_id} (user @{username})."
                    )
                    return ConversationHandler.END

            return PACKAGE_COMMAND_CODE
        except Exception as e:
            logger.error(f"Error in package_button: {e}")
            if query:
                await query.edit_message_text(f"Error updating user package: {str(e)}")
            return ConversationHandler.END

    async def callback_query_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
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
                    self.data = (
                        callback_data.encode("utf-8")
                        if isinstance(callback_data, str)
                        else callback_data
                    )
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
                await update.message.reply_text(
                    "Chat does not have an associated user."
                )
                return ConversationHandler.END

            # Check if chat has business package
            group_package = await self.group_package_service.get_package_by_chat_id(
                chat_id
            )
            if not group_package or group_package.package != ServicePackage.BUSINESS:
                current_package = (
                    group_package.package.value if group_package else "No package"
                )
                await update.message.reply_text(
                    f"Chat must have BUSINESS package to enable shift. Current package: {current_package}"
                )
                return ConversationHandler.END

            # Check if shift is already enabled
            if chat.enable_shift:  # type: ignore
                await update.message.reply_text(
                    "Shift is already enabled for this chat."
                )
                return ConversationHandler.END

            # Enable shift for the chat
            await self.chat_service.update_chat_enable_shift(chat_id, True)
            await update.message.reply_text(
                "Shift has been enabled successfully for this chat."
            )

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
            logger.error(f"Error in process_menu_chat_id: {e}", exc_info=True)

        return CALLBACK_QUERY_CODE

    async def callback_query_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Handle callback queries from inline buttons"""
        query = update.callback_query

        try:
            # We need to answer the callback query first to stop the loading indicator
            await query.answer()

            # Get the callback data
            callback_data = query.data

            # First, check if we're handling direct admin bot actions
            if callback_data in ["close_menu"]:
                await query.edit_message_text("Menu closed.")
                return ConversationHandler.END

            # Get chat_id from context or use message chat_id as fallback
            if context and context.user_data and "admin_chat_id" in context.user_data:
                chat_id = context.user_data["admin_chat_id"]
            else:
                # No stored chat ID from admin bot menu flow
                # This might be a global callback handler case
                await query.edit_message_text(
                    "Session expired. Please run /menu again."
                )
                return ConversationHandler.END

            # Prepare callback handlers for different report types
            if callback_data == "daily_summary":
                result = await self._handle_daily_summary_menu(chat_id, query)
                return CALLBACK_QUERY_CODE if result else ConversationHandler.END
            elif callback_data == "weekly_summary":
                result = await self._handle_report(chat_id, "weekly", query)
                return CALLBACK_QUERY_CODE if result else ConversationHandler.END
            elif callback_data == "monthly_summary":
                result = await self._handle_report(chat_id, "monthly", query)
                return CALLBACK_QUERY_CODE if result else ConversationHandler.END
            elif callback_data == "menu":
                # Return to main menu - recreate the menu buttons
                keyboard = [
                    [InlineKeyboardButton("ប្រចាំថ្ងៃ", callback_data="daily_summary")],
                    [InlineKeyboardButton("ប្រចាំសប្តាហ៍", callback_data="weekly_summary")],
                    [InlineKeyboardButton("ប្រចាំខែ", callback_data="monthly_summary")],
                    [InlineKeyboardButton("បិទ", callback_data="close_menu")],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.edit_message_text(
                    "ជ្រើសរើសរបាយការណ៍ប្រចាំ:", reply_markup=reply_markup
                )
                return CALLBACK_QUERY_CODE
            elif callback_data.startswith("summary_of_"):
                result = await self._handle_date_summary(chat_id, callback_data, query)
                return CALLBACK_QUERY_CODE if result else ConversationHandler.END
            elif callback_data == "report_per_shift":
                result = await self._handle_shift_report(chat_id, query)
                return CALLBACK_QUERY_CODE if result else ConversationHandler.END
            elif callback_data == "other_dates":
                result = await self._handle_other_dates(chat_id, query)
                return CALLBACK_QUERY_CODE if result else ConversationHandler.END

            # If we get here, it's an unknown callback
            await query.edit_message_text(f"Unhandled callback: {callback_data}")
            return CALLBACK_QUERY_CODE

        except Exception as e:
            logger.error(f"Error in callback_query_handler: {e}", exc_info=True)
            try:
                await query.message.reply_text(
                    f"Error processing button action: {str(e)}"
                )
            except:
                pass
            return ConversationHandler.END

    async def _handle_daily_summary_menu(self, chat_id: str, query):
        """Handle daily summary by showing date selection menu like normal bot"""
        try:
            from helper import DateUtils
            from datetime import timedelta

            chat = await self.chat_service.get_chat_by_chat_id(chat_id)
            if not chat:
                await query.edit_message_text(f"Chat {chat_id} not found.")
                return False

            today = DateUtils.now()
            keyboard = []

            # Check if shift is enabled for this chat
            shift_enabled = await self.chat_service.is_shift_enabled(int(chat_id))
            if shift_enabled:
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            "ប្រចាំវេន​ថ្ងៃ​នេះ", callback_data="report_per_shift"
                        )
                    ]
                )
                # Only show current date for shift-enabled chats
                label = today.strftime("ថ្ងៃ​នេះ")
                callback_value = today.strftime("%Y-%m-%d")
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            label, callback_data=f"summary_of_{callback_value}"
                        )
                    ]
                )
            else:
                # Show 3 days for non-shift chats
                for i in range(2, -1, -1):
                    day = today - timedelta(days=i)
                    label = day.strftime("%b %d")
                    callback_value = day.strftime("%Y-%m-%d")
                    keyboard.append(
                        [
                            InlineKeyboardButton(
                                label, callback_data=f"summary_of_{callback_value}"
                            )
                        ]
                    )

            keyboard.append(
                [InlineKeyboardButton("ថ្ងៃផ្សេងទៀត", callback_data="other_dates")]
            )
            keyboard.append([InlineKeyboardButton("ត្រឡប់ក្រោយ", callback_data="menu")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("ឆែករបាយការណ៍ថ្ងៃ:", reply_markup=reply_markup)
            return True

        except Exception as e:
            logger.error(f"Error in _handle_daily_summary_menu: {e}", exc_info=True)
            await query.edit_message_text(f"Error showing daily menu: {str(e)}")
            return False

    async def _handle_report(self, chat_id: str, report_type: str, query):
        """Handle generating a specific report type"""
        try:
            chat = await self.chat_service.get_chat_by_chat_id(chat_id)
            if not chat:
                await query.edit_message_text(f"Chat {chat_id} not found.")
                return False

            # Create return to menu button
            keyboard = [[InlineKeyboardButton("ត្រឡប់", callback_data="menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if report_type == "daily":
                # Call report generation logic or reuse from event_handler
                report = await self._generate_report(chat_id, "daily")
                await query.edit_message_text(report, reply_markup=reply_markup)
            elif report_type == "weekly":
                report = await self._generate_report(chat_id, "weekly")
                await query.edit_message_text(report, reply_markup=reply_markup)
            elif report_type == "monthly":
                report = await self._generate_report(chat_id, "monthly")
                await query.edit_message_text(report, reply_markup=reply_markup)

            return True
        except Exception as e:
            logger.error(f"Error in _handle_report: {e}", exc_info=True)
            await query.edit_message_text(
                f"Error generating {report_type} report: {str(e)}"
            )
            return False

    async def _handle_date_summary(self, chat_id: str, callback_data: str, query):
        """Handle date summary like normal bot"""
        try:
            from datetime import datetime, timedelta
            from models import IncomeService
            from helper import total_summary_report

            date_str = callback_data.replace("summary_of_", "")
            selected_date = datetime.strptime(date_str, "%Y-%m-%d")

            income_service = IncomeService()
            incomes = await income_service.get_income_by_date_and_chat_id(
                chat_id=int(chat_id),
                start_date=selected_date,
                end_date=selected_date + timedelta(days=1),
            )

            # Create return to daily menu button
            keyboard = [
                [InlineKeyboardButton("ត្រឡប់ក្រោយ", callback_data="daily_summary")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if not incomes:
                message = (
                    f"គ្មានប្រតិបត្តិការសម្រាប់ថ្ងៃទី {selected_date.strftime('%d %b %Y')} ទេ។"
                )
            else:
                period_text = f"ថ្ងៃទី {selected_date.strftime('%d %b %Y')}"
                formatted_title = f"សរុបប្រតិបត្តិការ {period_text}"
                message = total_summary_report(incomes, formatted_title)

            await query.edit_message_text(message, reply_markup=reply_markup)
            return True

        except Exception as e:
            logger.error(f"Error in _handle_date_summary: {e}", exc_info=True)
            await query.edit_message_text(f"Error generating date summary: {str(e)}")
            return False

    async def _handle_shift_report(self, chat_id: str, query):
        """Handle shift report - placeholder for now"""
        try:
            # For now, just show a placeholder message
            keyboard = [
                [InlineKeyboardButton("ត្រឡប់ក្រោយ", callback_data="daily_summary")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                "Shift report functionality not implemented yet.",
                reply_markup=reply_markup,
            )
            return True

        except Exception as e:
            logger.error(f"Error in _handle_shift_report: {e}", exc_info=True)
            await query.edit_message_text(f"Error: {str(e)}")
            return False

    async def _handle_other_dates(self, chat_id: str, query):
        """Handle other dates - placeholder for now"""
        try:
            # For now, just show a placeholder message
            keyboard = [
                [InlineKeyboardButton("ត្រឡប់ក្រោយ", callback_data="daily_summary")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                "Other dates functionality not implemented yet.",
                reply_markup=reply_markup,
            )
            return True

        except Exception as e:
            logger.error(f"Error in _handle_other_dates: {e}", exc_info=True)
            await query.edit_message_text(f"Error: {str(e)}")
            return False

    async def _generate_report(self, chat_id: str, report_type: str) -> str:
        """Generate report text by calling appropriate service methods"""
        from datetime import timedelta
        from models import IncomeService
        from helper import total_summary_report, DateUtils

        income_service = IncomeService()

        # Get current time using DateUtils for consistency
        now = DateUtils.now()

        if report_type == "daily":
            start_date = now
            end_date = now + timedelta(days=1)
            title = f"ថ្ងៃទី {now.strftime('%d %b %Y')}"
        elif report_type == "weekly":
            # Get start of week (Monday)
            start_of_week = now - timedelta(days=now.weekday())
            start_date = start_of_week
            end_date = now + timedelta(days=1)
            title = f"{start_of_week.strftime('%d')} - {now.strftime('%d %b %Y')}"
        elif report_type == "monthly":
            # First day of current month
            start_of_month = now.replace(day=1)
            start_date = start_of_month
            end_date = now + timedelta(days=1)
            title = f"{start_of_month.strftime('%d')} - {now.strftime('%d %b %Y')}"
        else:
            return "Invalid report type"

        # Get income data using the same method as normal bot
        incomes = await income_service.get_income_by_date_and_chat_id(
            chat_id=int(chat_id),
            start_date=start_date,
            end_date=end_date,
        )

        # If no data found, return no data message
        if not incomes:
            return f"គ្មានប្រតិបត្តិការសម្រាប់ {title} ទេ។"

        # Use the same formatting as normal bot
        period_text = title
        formatted_title = f"សរុបប្រតិបត្តិការ {period_text}"
        return total_summary_report(incomes, formatted_title)

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
            per_message=False,
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
            per_message=False,
        )

        # Package command handler with multiple states
        # Note: per_message=False warning is expected when mixing CallbackQueryHandler with other handler types
        package_handler = ConversationHandler(
            entry_points=[CommandHandler("package", self.package)],
            states={
                PACKAGE_SELECTION_CODE: [CallbackQueryHandler(self.package_button)],
                PACKAGE_COMMAND_CODE: [
                    MessageHandler(
                        filters.TEXT & filters.REPLY, self.process_package_input
                    ),
                    CallbackQueryHandler(self.package_button),
                ],
                USER_CONFIRMATION_CODE: [CallbackQueryHandler(self.package_button)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_chat=True,
            per_user=True,
            per_message=False,
        )

        enable_shift_handler = ConversationHandler(
            entry_points=[CommandHandler("enable_shift", self.enable_shift)],
            states={
                ENABLE_SHIFT_COMMAND_CODE: [
                    MessageHandler(
                        filters.TEXT & filters.REPLY, self.process_enable_shift_chat_id
                    )
                ],
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
                    CallbackQueryHandler(self.callback_query_handler)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_chat=True,
            per_user=True,
            per_message=False,
        )

        self.app.add_handler(activate_command_handler)
        self.app.add_handler(deactivate_command_handler)
        self.app.add_handler(package_handler)
        self.app.add_handler(enable_shift_handler)
        self.app.add_handler(menu_handler)

        # Remove the global callback query handler to avoid duplicate handling
        # self.app.add_handler(CallbackQueryHandler(self.callback_query_handler))
        logger.info("TelegramAdminBot handlers set up")

    async def start_polling(self) -> None:
        if not self.app:
            self.setup()

        assert self.app is not None
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()  # type: ignore
        logger.info("TelegramAdminBot started polling")
