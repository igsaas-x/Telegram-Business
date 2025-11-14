"""
Sender Management Command Handlers for Telegram Bot

Provides interactive commands for managing sender configurations:
- /sender - Main menu with:
  * Configure Sender (add, delete, list)
  * Reports (daily, weekly, monthly)
  * Cancel
"""

from calendar import monthrange
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from helper import force_log
from helper.dateutils import DateUtils
from services.conversation_state_manager import ConversationState, ConversationStateManager
from services.sender_category_service import SenderCategoryService
from services.sender_config_service import SenderConfigService
from services.sender_report_service import SenderReportService


class SenderCommandHandler:
    """Handler for sender management commands"""

    def __init__(self):
        self.conversation_manager = ConversationStateManager()
        self.sender_service = SenderConfigService()
        self.category_service = SenderCategoryService()
        self.report_service = SenderReportService()
        force_log("SenderCommandHandler initialized", "SenderCommandHandler")

    # ========== Main Menu ==========

    async def show_sender_menu(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Show the sender reports menu directly"""
        try:
            keyboard = [
                [InlineKeyboardButton("📅 Daily Report", callback_data="report_daily")],
                [InlineKeyboardButton("📆 Weekly Report", callback_data="report_weekly")],
                [InlineKeyboardButton("📊 Monthly Report", callback_data="report_monthly")],
                [InlineKeyboardButton("❌ Cancel", callback_data="sender_cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            message_text = "📊 Sender Reports\n\nPlease select a report type:"

            # Check if this is a callback query or a command
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    message_text,
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(
                    message_text,
                    reply_markup=reply_markup
                )
        except Exception as e:
            force_log(f"Error in show_sender_menu: {e}", "SenderCommandHandler", "ERROR")
            import traceback
            force_log(f"Traceback: {traceback.format_exc()}", "SenderCommandHandler", "ERROR")

    async def show_setup_menu(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Show the setup/configure sender menu"""
        try:
            keyboard = [
                [InlineKeyboardButton("📋 List Senders", callback_data="sender_list")],
                [InlineKeyboardButton("➕ Add Sender", callback_data="sender_add")],
                [InlineKeyboardButton("🗑 Delete Sender", callback_data="sender_delete")],
                # [InlineKeyboardButton("🏷️ Manage Categories", callback_data="category_menu")],
                [InlineKeyboardButton("❌ Cancel", callback_data="sender_cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            message_text = "⚙️ Configure Sender\n\nPlease select an option:"

            # Check if this is a callback query or a command
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    message_text,
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(
                    message_text,
                    reply_markup=reply_markup
                )
        except Exception as e:
            force_log(f"Error in show_setup_menu: {e}", "SenderCommandHandler", "ERROR")
            import traceback
            force_log(f"Traceback: {traceback.format_exc()}", "SenderCommandHandler", "ERROR")


    async def handle_callback_query(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle callback queries from inline keyboards"""
        try:
            query = update.callback_query
            callback_data = query.data

            force_log(f"Callback query received: {callback_data}", "SenderCommandHandler")

            # Cancel action
            if callback_data == "sender_cancel":
                await query.answer()
                await query.edit_message_text("❌ Cancelled")

            # Back to setup menu
            elif callback_data == "setup_back":
                await self.show_setup_menu(update, context)

            # Configure/Setup menu actions
            elif callback_data == "sender_list":
                await self.sender_list_inline(update, context)
            elif callback_data == "sender_add":
                await self.sender_add_start_inline(update, context)
            elif callback_data == "sender_delete":
                await self.sender_delete_start_inline(update, context)

            # Reports actions
            elif callback_data == "report_daily":
                await self.sender_report_inline(update, context)
            elif callback_data == "report_weekly":
                await self.show_weekly_selection(update, context)
            elif callback_data == "report_monthly":
                await self.show_monthly_selection(update, context)
            elif callback_data.startswith("sender_week_"):
                await self.generate_weekly_report(update, context)
            elif callback_data.startswith("sender_month_"):
                await self.generate_monthly_report(update, context)

            # Category selection during sender add
            elif callback_data.startswith("sender_add_category_"):
                await self.sender_add_handle_category_callback(update, context)

            # Cancel conversation callbacks
            elif callback_data in ["sender_add_cancel", "sender_delete_cancel", "sender_update_cancel"]:
                await query.answer()
                user_id = update.effective_user.id
                chat_id = update.effective_chat.id
                self.conversation_manager.end_conversation(chat_id, user_id)
                await self.show_setup_menu(update, context)

        except Exception as e:
            force_log(f"Error in handle_callback_query: {e}", "SenderCommandHandler", "ERROR")
            import traceback
            force_log(f"Traceback: {traceback.format_exc()}", "SenderCommandHandler", "ERROR")

    # ========== Inline Menu Actions ==========

    async def sender_list_inline(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """List all configured senders (inline version)"""
        try:
            query = update.callback_query
            await query.answer()
            chat_id = update.effective_chat.id

            # Get all senders
            senders = await self.sender_service.get_senders(chat_id)

            if not senders:
                keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="setup_back")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "📋 Sender List\n\n"
                    "❌ No senders configured yet.\n\n"
                    "Use Add Sender to add a sender.",
                    reply_markup=reply_markup
                )
                return

            # Format sender list
            sender_lines = []
            for i, sender in enumerate(senders, 1):
                name = sender.sender_name or "No name"
                sender_lines.append(f"{i}. *{sender.sender_account_number} - {name}")

            sender_list = "\n".join(sender_lines)

            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="setup_back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                f"📋 Sender List ({len(senders)} total)\n\n"
                f"{sender_list}",
                reply_markup=reply_markup
            )

        except Exception as e:
            force_log(f"Error in sender_list_inline: {e}", "SenderCommandHandler", "ERROR")

    async def sender_add_start_inline(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Start the add sender flow from inline menu"""
        try:
            query = update.callback_query
            await query.answer()
            chat_id = update.effective_chat.id
            user_id = update.effective_user.id

            force_log(
                f"Add sender started by user {user_id} in chat {chat_id}",
                "SenderCommandHandler"
            )

            # Start conversation
            self.conversation_manager.start_conversation(
                chat_id, user_id, "sender_add", ConversationState.WAITING_FOR_ACCOUNT_NUMBER
            )

            await query.edit_message_text(
                "➕ Add New Sender\n\n"
                "Please reply with the account number (last 3 digits):\n\n"
                "Example: 708"
            )

        except Exception as e:
            force_log(f"Error in sender_add_start_inline: {e}", "SenderCommandHandler", "ERROR")

    async def sender_delete_start_inline(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Start the delete sender flow from inline menu"""
        try:
            query = update.callback_query
            await query.answer()
            chat_id = update.effective_chat.id
            user_id = update.effective_user.id

            # Get all senders
            senders = await self.sender_service.get_senders(chat_id)

            if not senders:
                keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="setup_back")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "❌ No senders configured yet.\n\n"
                    "Use Add Sender to add a sender first.",
                    reply_markup=reply_markup
                )
                return

            # Format sender list
            sender_list = "\n".join(
                [
                    f"• *{s.sender_account_number} - {s.sender_name or 'No name'}"
                    for s in senders
                ]
            )

            # Start conversation
            self.conversation_manager.start_conversation(
                chat_id, user_id, "sender_delete", ConversationState.WAITING_FOR_ACCOUNT_NUMBER
            )

            await query.edit_message_text(
                f"🗑 Delete Sender\n\n"
                f"Current senders:\n{sender_list}\n\n"
                f"Please reply with the account number (last 3 digits) to delete:"
            )

        except Exception as e:
            force_log(f"Error in sender_delete_start_inline: {e}", "SenderCommandHandler", "ERROR")

    async def sender_report_inline(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Generate daily sender report (inline version)"""
        try:
            query = update.callback_query
            await query.answer()
            chat_id = update.effective_chat.id

            # Check if any senders configured
            senders = await self.sender_service.get_senders(chat_id)
            if not senders:
                await query.answer("❌ No senders configured. Use /setup to add senders first.", show_alert=True)
                return

            # Generate report
            telegram_username = update.effective_user.username or "Admin"
            report = await self.report_service.generate_daily_report(chat_id, telegram_username=telegram_username)

            await query.edit_message_text(report, parse_mode='HTML')

        except Exception as e:
            force_log(f"Error in sender_report_inline: {e}", "SenderCommandHandler", "ERROR")

    async def show_weekly_selection(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Show weekly report selection menu"""
        try:
            query = update.callback_query
            await query.answer()

            now = DateUtils.now()
            current_year = now.year
            current_month = now.month

            _, days_in_month = monthrange(current_year, current_month)

            keyboard = []

            # Week 1: 1-7
            week1_end = min(7, days_in_month)
            keyboard.append([InlineKeyboardButton(f"សប្តាហ៍ 1 (1-{week1_end})", callback_data=f"sender_week_{current_year}-{current_month:02d}-1")])

            # Week 2: 8-14
            if days_in_month >= 8:
                week2_end = min(14, days_in_month)
                keyboard.append([InlineKeyboardButton(f"សប្តាហ៍ 2 (8-{week2_end})", callback_data=f"sender_week_{current_year}-{current_month:02d}-2")])

            # Week 3: 15-21
            if days_in_month >= 15:
                week3_end = min(21, days_in_month)
                keyboard.append([InlineKeyboardButton(f"សប្តាហ៍ 3 (15-{week3_end})", callback_data=f"sender_week_{current_year}-{current_month:02d}-3")])

            # Week 4: 22-end of month
            if days_in_month >= 22:
                keyboard.append([InlineKeyboardButton(f"សប្តាហ៍ 4 (22-{days_in_month})", callback_data=f"sender_week_{current_year}-{current_month:02d}-4")])

            keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="sender_cancel")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(f"📆 របាយការណ៍ប្រចាំសប្តាហ៍ - {now.strftime('%B %Y')}\n\nជ្រើសរើសសប្តាហ៍:", reply_markup=reply_markup)

        except Exception as e:
            force_log(f"Error in show_weekly_selection: {e}", "SenderCommandHandler", "ERROR")

    async def show_monthly_selection(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Show monthly report selection menu"""
        try:
            query = update.callback_query
            await query.answer()

            now = DateUtils.now()
            year = now.year
            keyboard = []

            for month in range(1, 13, 2):
                month_date_1 = datetime(year, month, 1)
                label_1 = month_date_1.strftime("%B %Y")
                callback_value_1 = month_date_1.strftime("%Y-%m")

                row = [InlineKeyboardButton(label_1, callback_data=f"sender_month_{callback_value_1}")]

                if month + 1 <= 12:
                    month_date_2 = datetime(year, month + 1, 1)
                    label_2 = month_date_2.strftime("%B %Y")
                    callback_value_2 = month_date_2.strftime("%Y-%m")
                    row.append(InlineKeyboardButton(label_2, callback_data=f"sender_month_{callback_value_2}"))

                keyboard.append(row)

            keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="sender_cancel")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("ជ្រើសរើសខែ:", reply_markup=reply_markup)

        except Exception as e:
            force_log(f"Error in show_monthly_selection: {e}", "SenderCommandHandler", "ERROR")

    async def generate_weekly_report(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Generate weekly sender report"""
        try:
            query = update.callback_query
            await query.answer()
            chat_id = update.effective_chat.id

            # Check if any senders configured
            senders = await self.sender_service.get_senders(chat_id)
            if not senders:
                await query.answer("❌ No senders configured. Use /setup to add senders first.", show_alert=True)
                return

            # Parse callback data: YYYY-MM-W format
            callback_data = query.data
            date_parts = callback_data.replace("sender_week_", "").split("-")
            year = int(date_parts[0])
            month = int(date_parts[1])
            week_number = int(date_parts[2])

            # Calculate start and end dates based on week number
            _, days_in_month = monthrange(year, month)

            if week_number == 1:
                start_day = 1
                end_day = min(7, days_in_month)
            elif week_number == 2:
                start_day = 8
                end_day = min(14, days_in_month)
            elif week_number == 3:
                start_day = 15
                end_day = min(21, days_in_month)
            elif week_number == 4:
                start_day = 22
                end_day = days_in_month
            else:
                raise ValueError(f"Invalid week number: {week_number}")

            start_date = datetime(year, month, start_day)
            end_date = datetime(year, month, end_day) + timedelta(days=1)  # End of day

            # Generate report
            telegram_username = update.effective_user.username or "Admin"
            report = await self.report_service.generate_weekly_report(
                chat_id, start_date, end_date, telegram_username=telegram_username
            )

            await query.edit_message_text(report, parse_mode='HTML')

        except Exception as e:
            force_log(f"Error in generate_weekly_report: {e}", "SenderCommandHandler", "ERROR")
            import traceback
            force_log(f"Traceback: {traceback.format_exc()}", "SenderCommandHandler", "ERROR")

    async def generate_monthly_report(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Generate monthly sender report"""
        try:
            query = update.callback_query
            await query.answer()
            chat_id = update.effective_chat.id

            # Check if any senders configured
            senders = await self.sender_service.get_senders(chat_id)
            if not senders:
                await query.answer("❌ No senders configured. Use /setup to add senders first.", show_alert=True)
                return

            # Parse callback data: YYYY-MM format
            callback_data = query.data
            start_date = datetime.strptime(
                callback_data.replace("sender_month_", ""), "%Y-%m"
            )

            _, last_day = monthrange(start_date.year, start_date.month)
            end_date = start_date.replace(day=last_day) + timedelta(days=1)

            # Generate report
            telegram_username = update.effective_user.username or "Admin"
            report = await self.report_service.generate_monthly_report(
                chat_id, start_date, end_date, telegram_username=telegram_username
            )

            await query.edit_message_text(report, parse_mode='HTML')

        except Exception as e:
            force_log(f"Error in generate_monthly_report: {e}", "SenderCommandHandler", "ERROR")
            import traceback
            force_log(f"Traceback: {traceback.format_exc()}", "SenderCommandHandler", "ERROR")

    # ========== /sender_add Command ==========

    async def sender_add_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Start the /sender_add interactive flow"""
        try:
            chat_id = update.effective_chat.id
            user_id = update.effective_user.id

            force_log(
                f"/sender_add started by user {user_id} in chat {chat_id}",
                "SenderCommandHandler"
            )

            # Start conversation
            self.conversation_manager.start_conversation(
                chat_id, user_id, "sender_add", ConversationState.WAITING_FOR_ACCOUNT_NUMBER
            )

            force_log(
                f"Conversation state created for user {user_id}: WAITING_FOR_ACCOUNT_NUMBER",
                "SenderCommandHandler"
            )

            await update.message.reply_text(
                "➕ Add New Sender\n\n"
                "Please reply with the account number (last 3 digits):\n\n"
                "Example: 708\n\n"
                "Send /cancel to cancel this operation."
            )

        except Exception as e:
            force_log(f"Error in sender_add_start: {e}", "SenderCommandHandler", "ERROR")
            import traceback
            force_log(f"Traceback: {traceback.format_exc()}", "SenderCommandHandler", "ERROR")
            await update.message.reply_text(
                "❌ An error occurred. Please try again."
            )

    async def sender_add_handle_account(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle account number input for /sender_add"""
        try:
            chat_id = update.effective_chat.id
            user_id = update.effective_user.id

            # Check if user is in this conversation
            state = self.conversation_manager.get_state(chat_id, user_id)
            if state != ConversationState.WAITING_FOR_ACCOUNT_NUMBER:
                return

            # Validate account number
            account_number = update.message.text.strip()

            if not account_number.isdigit() or len(account_number) != 3:
                await update.message.reply_text(
                    "❌ Invalid account number. Must be exactly 3 digits.\n\n"
                    "Please try again or send /cancel to cancel."
                )
                return

            # Check if sender already exists
            existing = await self.sender_service.get_sender_by_account_number(
                chat_id, account_number
            )
            if existing:
                await update.message.reply_text(
                    f"❌ Sender *{account_number} already exists.\n\n"
                    f"Name: {existing.sender_name or 'No name'}\n\n"
                    "Please use /sender_update to update or try a different account number."
                )
                self.conversation_manager.end_conversation(chat_id, user_id)
                return

            # Update conversation state
            self.conversation_manager.update_state(
                chat_id,
                user_id,
                ConversationState.WAITING_FOR_NAME,
                account_number=account_number,
            )

            await update.message.reply_text(
                f"✅ Account number: *{account_number}\n\n"
                "Please reply with the account name:\n\n"
                "Example: John Doe\n\n"
                "Send /cancel to cancel this operation."
            )

        except Exception as e:
            force_log(f"Error in sender_add_handle_account: {e}", "SenderCommandHandler", "ERROR")
            await update.message.reply_text(
                "❌ An error occurred. Please try again."
            )

    async def sender_add_handle_name(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle account name input for /sender_add"""
        try:
            chat_id = update.effective_chat.id
            user_id = update.effective_user.id

            # Check if user is in this conversation
            state = self.conversation_manager.get_state(chat_id, user_id)
            if state != ConversationState.WAITING_FOR_NAME:
                return

            # Get conversation data
            data = self.conversation_manager.get_data(chat_id, user_id)
            if not data or "account_number" not in data:
                await update.message.reply_text("❌ Session expired. Please start again with /sender_add")
                self.conversation_manager.end_conversation(chat_id, user_id)
                return

            account_number = data["account_number"]
            account_name = update.message.text.strip()

            # Move to nickname step
            self.conversation_manager.update_state(
                chat_id,
                user_id,
                ConversationState.WAITING_FOR_NICKNAME,
                account_number=account_number,
                account_name=account_name,
            )

            await update.message.reply_text(
                f"✅ Account number: *{account_number}\n"
                f"✅ Account name: {account_name}\n\n"
                "Please reply with a nickname (or type 'skip' to use account name):\n\n"
                "Example: Johnny\n\n"
                "Send /cancel to cancel this operation."
            )

        except Exception as e:
            force_log(f"Error in sender_add_handle_name: {e}", "SenderCommandHandler", "ERROR")
            await update.message.reply_text(
                "❌ An error occurred. Please try again."
            )

    async def sender_add_handle_nickname(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle nickname input for /sender_add"""
        try:
            chat_id = update.effective_chat.id
            user_id = update.effective_user.id

            # Check if user is in this conversation
            state = self.conversation_manager.get_state(chat_id, user_id)
            if state != ConversationState.WAITING_FOR_NICKNAME:
                return

            # Get conversation data
            data = self.conversation_manager.get_data(chat_id, user_id)
            if not data or "account_number" not in data or "account_name" not in data:
                await update.message.reply_text("❌ Session expired. Please start again with /sender_add")
                self.conversation_manager.end_conversation(chat_id, user_id)
                return

            account_number = data["account_number"]
            account_name = data["account_name"]
            nickname_input = update.message.text.strip()

            # Handle 'skip' to use account name as display name
            nickname = None if nickname_input.lower() == 'skip' else nickname_input

            # Get all categories
            categories = await self.category_service.list_categories(chat_id)

            if not categories:
                # No categories available - must create categories first
                await update.message.reply_text(
                    "❌ No categories found!\n\n"
                    "All senders must belong to a category. "
                    "Please ask an admin to create categories first using /category command.\n\n"
                    "Operation cancelled."
                )
                self.conversation_manager.end_conversation(chat_id, user_id)
                return

            # Update conversation state to wait for category selection
            self.conversation_manager.update_state(
                chat_id,
                user_id,
                ConversationState.WAITING_FOR_CATEGORY_SELECTION,
                account_number=account_number,
                account_name=account_name,
                nickname=nickname,
            )

            # Create inline keyboard with category buttons (no skip option)
            keyboard = []
            for category in categories:
                keyboard.append([
                    InlineKeyboardButton(
                        category.category_name,
                        callback_data=f"sender_add_category_{category.id}"
                    )
                ])
            reply_markup = InlineKeyboardMarkup(keyboard)

            display_name = nickname if nickname else account_name
            await update.message.reply_text(
                f"✅ Account number: *{account_number}\n"
                f"✅ Account name: {account_name}\n"
                f"✅ Display name: {display_name}\n\n"
                f"🏷️ Please select a category:",
                reply_markup=reply_markup
            )

        except Exception as e:
            force_log(f"Error in sender_add_handle_nickname: {e}", "SenderCommandHandler", "ERROR")
            await update.message.reply_text(
                "❌ An error occurred. Please try again."
            )

    async def sender_add_handle_category_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle category selection button click for /sender_add"""
        try:
            query = update.callback_query
            await query.answer()

            chat_id = update.effective_chat.id
            user_id = update.effective_user.id

            # Check if user is in this conversation
            state = self.conversation_manager.get_state(chat_id, user_id)
            if state != ConversationState.WAITING_FOR_CATEGORY_SELECTION:
                await query.edit_message_text("❌ Session expired. Please start again.")
                return

            # Get conversation data
            data = self.conversation_manager.get_data(chat_id, user_id)
            if not data or "account_number" not in data or "account_name" not in data:
                await query.edit_message_text("❌ Session expired. Please start again.")
                self.conversation_manager.end_conversation(chat_id, user_id)
                return

            account_number = data["account_number"]
            account_name = data["account_name"]
            nickname = data.get("nickname")  # May be None

            # Parse callback data: sender_add_category_{id}
            callback_data = query.data
            category_id = int(callback_data.replace("sender_add_category_", ""))

            # Get category to get its name
            category = await self.category_service.get_category_by_id(category_id)
            if not category:
                await query.edit_message_text("❌ Category not found. Please try again.")
                self.conversation_manager.end_conversation(chat_id, user_id)
                return

            # Create sender with account name
            success, message = await self.sender_service.add_sender(
                chat_id, account_number, account_name
            )

            if success:
                # Set nickname if provided
                if nickname:
                    await self.category_service.update_sender_nickname(
                        chat_id, account_number, nickname
                    )

                # Assign category to the newly created sender
                assign_success, assign_message = await self.category_service.assign_sender_to_category(
                    chat_id, account_number, category.category_name
                )

                display_name = nickname if nickname else account_name
                if assign_success:
                    await query.edit_message_text(
                        f"{message}\n"
                        f"{assign_message}\n"
                        f"Display name: {display_name}"
                    )
                else:
                    await query.edit_message_text(
                        f"{message}\n"
                        f"⚠️ {assign_message}\n"
                        f"Display name: {display_name}"
                    )
            else:
                await query.edit_message_text(message)

            # End conversation
            self.conversation_manager.end_conversation(chat_id, user_id)

        except Exception as e:
            force_log(f"Error in sender_add_handle_category_callback: {e}", "SenderCommandHandler", "ERROR")
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    "❌ An error occurred. Please try again."
                )

    # ========== /sender_delete Command ==========

    async def sender_delete_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Start the /sender_delete interactive flow"""
        try:
            chat_id = update.effective_chat.id
            user_id = update.effective_user.id

            # Get all senders
            senders = await self.sender_service.get_senders(chat_id)

            if not senders:
                await update.message.reply_text(
                    "❌ No senders configured yet.\n\n"
                    "Use /sender_add to add a sender first."
                )
                return

            # Format sender list
            sender_list = "\n".join(
                [
                    f"• *{s.sender_account_number} - {s.sender_name or 'No name'}"
                    for s in senders
                ]
            )

            # Start conversation
            self.conversation_manager.start_conversation(
                chat_id, user_id, "sender_delete", ConversationState.WAITING_FOR_ACCOUNT_NUMBER
            )

            await update.message.reply_text(
                f"🗑 Delete Sender\n\n"
                f"Current senders:\n{sender_list}\n\n"
                f"Please reply with the account number (last 3 digits) to delete:\n\n"
                f"Send /cancel to cancel this operation."
            )

        except Exception as e:
            force_log(f"Error in sender_delete_start: {e}", "SenderCommandHandler", "ERROR")
            await update.message.reply_text(
                "❌ An error occurred. Please try again."
            )

    async def sender_delete_handle_account(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle account number input for /sender_delete"""
        try:
            chat_id = update.effective_chat.id
            user_id = update.effective_user.id

            # Check if user is in delete conversation
            state = self.conversation_manager.get_state(chat_id, user_id)
            command = self.conversation_manager.get_command(chat_id, user_id)

            if state != ConversationState.WAITING_FOR_ACCOUNT_NUMBER or command != "sender_delete":
                return

            # Validate account number
            account_number = update.message.text.strip()

            if not account_number.isdigit() or len(account_number) != 3:
                await update.message.reply_text(
                    "❌ Invalid account number. Must be exactly 3 digits.\n\n"
                    "Please try again or send /cancel to cancel."
                )
                return

            # Delete sender
            success, message = await self.sender_service.delete_sender(
                chat_id, account_number
            )

            await update.message.reply_text(message)

            # End conversation
            self.conversation_manager.end_conversation(chat_id, user_id)

        except Exception as e:
            force_log(f"Error in sender_delete_handle_account: {e}", "SenderCommandHandler", "ERROR")
            await update.message.reply_text(
                "❌ An error occurred. Please try again."
            )

    # ========== /sender_update Command ==========

    async def sender_update_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Start the /sender_update interactive flow"""
        try:
            chat_id = update.effective_chat.id
            user_id = update.effective_user.id

            # Get all senders
            senders = await self.sender_service.get_senders(chat_id)

            if not senders:
                await update.message.reply_text(
                    "❌ No senders configured yet.\n\n"
                    "Use /sender_add to add a sender first."
                )
                return

            # Format sender list
            sender_list = "\n".join(
                [
                    f"• *{s.sender_account_number} - {s.sender_name or 'No name'}"
                    for s in senders
                ]
            )

            # Start conversation
            self.conversation_manager.start_conversation(
                chat_id, user_id, "sender_update", ConversationState.WAITING_FOR_ACCOUNT_NUMBER
            )

            await update.message.reply_text(
                f"✏️ Update Sender Name\n\n"
                f"Current senders:\n{sender_list}\n\n"
                f"Please reply with the account number (last 3 digits) to update:\n\n"
                f"Send /cancel to cancel this operation."
            )

        except Exception as e:
            force_log(f"Error in sender_update_start: {e}", "SenderCommandHandler", "ERROR")
            await update.message.reply_text(
                "❌ An error occurred. Please try again."
            )

    async def sender_update_handle_account(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle account number input for /sender_update"""
        try:
            chat_id = update.effective_chat.id
            user_id = update.effective_user.id

            # Check if user is in update conversation
            state = self.conversation_manager.get_state(chat_id, user_id)
            command = self.conversation_manager.get_command(chat_id, user_id)

            if state != ConversationState.WAITING_FOR_ACCOUNT_NUMBER or command != "sender_update":
                return

            # Validate account number
            account_number = update.message.text.strip()

            if not account_number.isdigit() or len(account_number) != 3:
                await update.message.reply_text(
                    "❌ Invalid account number. Must be exactly 3 digits.\n\n"
                    "Please try again or send /cancel to cancel."
                )
                return

            # Check if sender exists
            sender = await self.sender_service.get_sender_by_account_number(
                chat_id, account_number
            )
            if not sender:
                await update.message.reply_text(
                    f"❌ Sender *{account_number} not found.\n\n"
                    "Please try again or send /cancel to cancel."
                )
                return

            # Update conversation state
            self.conversation_manager.update_state(
                chat_id,
                user_id,
                ConversationState.WAITING_FOR_NEW_NAME,
                account_number=account_number,
                current_name=sender.sender_name,
            )

            current_name = sender.sender_name or "No name"
            await update.message.reply_text(
                f"Current name for *{account_number}: {current_name}\n\n"
                f"Please reply with the new name:\n\n"
                f"Send /cancel to cancel this operation."
            )

        except Exception as e:
            force_log(f"Error in sender_update_handle_account: {e}", "SenderCommandHandler", "ERROR")
            await update.message.reply_text(
                "❌ An error occurred. Please try again."
            )

    async def sender_update_handle_name(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle new name input for /sender_update"""
        try:
            chat_id = update.effective_chat.id
            user_id = update.effective_user.id

            # Check if user is in this conversation
            state = self.conversation_manager.get_state(chat_id, user_id)
            if state != ConversationState.WAITING_FOR_NEW_NAME:
                return

            # Get conversation data
            data = self.conversation_manager.get_data(chat_id, user_id)
            if not data or "account_number" not in data:
                await update.message.reply_text("❌ Session expired. Please start again with /sender_update")
                self.conversation_manager.end_conversation(chat_id, user_id)
                return

            account_number = data["account_number"]
            new_name = update.message.text.strip()

            # Update sender
            success, message = await self.sender_service.update_sender(
                chat_id, account_number, new_name
            )

            await update.message.reply_text(message)

            # End conversation
            self.conversation_manager.end_conversation(chat_id, user_id)

        except Exception as e:
            force_log(f"Error in sender_update_handle_name: {e}", "SenderCommandHandler", "ERROR")
            await update.message.reply_text(
                "❌ An error occurred. Please try again."
            )

    # ========== /sender_list Command ==========

    async def sender_list(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """List all configured senders"""
        try:
            chat_id = update.effective_chat.id

            # Get all senders
            senders = await self.sender_service.get_senders(chat_id)

            if not senders:
                await update.message.reply_text(
                    "📋 Sender List\n\n"
                    "❌ No senders configured yet.\n\n"
                    "Use /sender_add to add a sender."
                )
                return

            # Format sender list
            sender_lines = []
            for i, sender in enumerate(senders, 1):
                name = sender.sender_name or "No name"
                sender_lines.append(f"{i}. *{sender.sender_account_number} - {name}")

            sender_list = "\n".join(sender_lines)

            await update.message.reply_text(
                f"📋 Sender List ({len(senders)} total)\n\n"
                f"{sender_list}\n\n"
                f"Commands:\n"
                f"• /sender_add - Add new sender\n"
                f"• /sender_update - Update sender name\n"
                f"• /sender_delete - Delete sender\n"
                f"• /sender_report - View today's report"
            )

        except Exception as e:
            force_log(f"Error in sender_list: {e}", "SenderCommandHandler", "ERROR")
            await update.message.reply_text(
                "❌ An error occurred. Please try again."
            )

    # ========== /sender_report Command ==========

    async def sender_report(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Generate daily sender report"""
        try:
            chat_id = update.effective_chat.id

            # Check if any senders configured
            senders = await self.sender_service.get_senders(chat_id)
            if not senders:
                await update.message.reply_text(
                    "❌ No senders configured yet.\n\n"
                    "Use /sender_add to add senders first, then use /sender_report to view reports."
                )
                return

            # Generate report
            telegram_username = update.effective_user.username or "Admin"
            report = await self.report_service.generate_daily_report(chat_id, telegram_username=telegram_username)

            await update.message.reply_text(report, parse_mode='HTML')

        except Exception as e:
            force_log(f"Error in sender_report: {e}", "SenderCommandHandler", "ERROR")
            await update.message.reply_text(
                "❌ An error occurred generating the report. Please try again."
            )

    # ========== /cancel Command ==========

    async def cancel_conversation(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Cancel current conversation"""
        try:
            chat_id = update.effective_chat.id
            user_id = update.effective_user.id

            # Try to cancel conversation
            cancelled = self.conversation_manager.cancel_conversation(chat_id, user_id)

            if cancelled:
                await update.message.reply_text(
                    "❌ Operation cancelled.\n\n"
                    "Use /sender_list to see available commands."
                )
            else:
                await update.message.reply_text(
                    "ℹ️ No active operation to cancel."
                )

        except Exception as e:
            force_log(f"Error in cancel_conversation: {e}", "SenderCommandHandler", "ERROR")

    # ========== Message Router ==========

    async def handle_text_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Route text messages based on conversation state"""
        try:
            chat_id = update.effective_chat.id
            user_id = update.effective_user.id
            message_text = update.message.text if update.message else ""

            # Get current state and command
            state = self.conversation_manager.get_state(chat_id, user_id)
            command = self.conversation_manager.get_command(chat_id, user_id)

            # Log for debugging
            force_log(
                f"Text message received: user={user_id}, chat={chat_id}, state={state}, command={command}, text='{message_text[:50]}'",
                "SenderCommandHandler"
            )

            if not state or not command:
                force_log(
                    f"No active conversation for user {user_id} in chat {chat_id}",
                    "SenderCommandHandler"
                )
                return  # Not in a conversation

            # Route based on state and command
            if command == "sender_add":
                if state == ConversationState.WAITING_FOR_ACCOUNT_NUMBER:
                    force_log(f"Routing to sender_add_handle_account for user {user_id}", "SenderCommandHandler")
                    await self.sender_add_handle_account(update, context)
                elif state == ConversationState.WAITING_FOR_NAME:
                    force_log(f"Routing to sender_add_handle_name for user {user_id}", "SenderCommandHandler")
                    await self.sender_add_handle_name(update, context)
                elif state == ConversationState.WAITING_FOR_NICKNAME:
                    force_log(f"Routing to sender_add_handle_nickname for user {user_id}", "SenderCommandHandler")
                    await self.sender_add_handle_nickname(update, context)
                # WAITING_FOR_CATEGORY_SELECTION is handled by callback, not text

            elif command == "sender_delete":
                if state == ConversationState.WAITING_FOR_ACCOUNT_NUMBER:
                    force_log(f"Routing to sender_delete_handle_account for user {user_id}", "SenderCommandHandler")
                    await self.sender_delete_handle_account(update, context)

            elif command == "sender_update":
                if state == ConversationState.WAITING_FOR_ACCOUNT_NUMBER:
                    force_log(f"Routing to sender_update_handle_account for user {user_id}", "SenderCommandHandler")
                    await self.sender_update_handle_account(update, context)
                elif state == ConversationState.WAITING_FOR_NEW_NAME:
                    force_log(f"Routing to sender_update_handle_name for user {user_id}", "SenderCommandHandler")
                    await self.sender_update_handle_name(update, context)

        except Exception as e:
            force_log(f"Error in handle_text_message: {e}", "SenderCommandHandler", "ERROR")
            import traceback
            force_log(f"Traceback: {traceback.format_exc()}", "SenderCommandHandler", "ERROR")
