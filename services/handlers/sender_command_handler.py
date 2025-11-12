"""
Sender Management Command Handlers for Telegram Bot

Provides interactive commands for managing sender configurations:
- /sender - Main menu with:
  * Configure Sender (add, delete, list)
  * Reports (daily, weekly, monthly)
  * Cancel
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from helper import force_log
from services.conversation_state_manager import ConversationState, ConversationStateManager
from services.sender_config_service import SenderConfigService
from services.sender_report_service import SenderReportService


class SenderCommandHandler:
    """Handler for sender management commands"""

    def __init__(self):
        self.conversation_manager = ConversationStateManager()
        self.sender_service = SenderConfigService()
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
                [InlineKeyboardButton("📆 Weekly Report (Coming Soon)", callback_data="report_weekly_disabled")],
                [InlineKeyboardButton("📊 Monthly Report (Coming Soon)", callback_data="report_monthly_disabled")],
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
            elif callback_data in ["report_weekly_disabled", "report_monthly_disabled"]:
                await query.answer("This feature is coming soon!", show_alert=True)

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
                "Please reply with the sender name:\n\n"
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
        """Handle name input for /sender_add"""
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
            sender_name = update.message.text.strip()

            # Add sender to database
            success, message = await self.sender_service.add_sender(
                chat_id, account_number, sender_name
            )

            await update.message.reply_text(message)

            # End conversation
            self.conversation_manager.end_conversation(chat_id, user_id)

        except Exception as e:
            force_log(f"Error in sender_add_handle_name: {e}", "SenderCommandHandler", "ERROR")
            await update.message.reply_text(
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
