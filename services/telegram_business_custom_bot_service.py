import asyncio
import logging

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    Application,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from helper import force_log
from helper.custom_summary_report_helper import custom_summary_report_with_breakdown
from models import Chat
from services.chat_service import ChatService
from services.group_package_service import GroupPackageService
from services.handlers.menu_handler import MenuHandler
from services.private_bot_group_binding_service import PrivateBotGroupBindingService

# Get logger
logger = logging.getLogger(__name__)

# Conversation state codes for custom bot
START_MENU_CODE = 3000
BIND_GROUP_CODE = 3001
BIND_GROUP_SELECTION_CODE = 3002
BIND_GROUP_SEARCH_CODE = 3003
MENU_SELECTION_CODE = 3004
REPORT_CALLBACK_CODE = 3005


class AutosumBusinessCustomBot:
    """
    Custom business bot for viewing summary reports with revenue breakdown
    Similar to private bot but with enhanced breakdown functionality
    """

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.app: Application | None = None
        self.binding_service = PrivateBotGroupBindingService()
        self.chat_service = ChatService()
        self.group_package_service = GroupPackageService()
        self.menu_handler = MenuHandler()

        force_log("AutosumBusinessCustomBot initialized with token", "AutosumBusinessCustomBot")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        # Check if user is authorized
        allowed_users = ["HK_688", "houhokheng", "autosum_kh"]
        username = update.effective_user.username if update.effective_user else None

        if not username or username not in allowed_users:
            await update.message.reply_text(
                "🚫 Access denied. Please contact the administrator for access. https://t.me/HK_688"
            )
            return ConversationHandler.END

        keyboard = [
            [InlineKeyboardButton("🔗 Bind Group", callback_data="start_bind")],
            [InlineKeyboardButton("📋 List Groups", callback_data="start_list")],
            [InlineKeyboardButton("📊 View Reports", callback_data="start_menu")],
            [InlineKeyboardButton("🔓 Unbind Group", callback_data="start_unbind")],
            [InlineKeyboardButton("❌ Cancel", callback_data="close_conversation")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🏢 *Welcome to Autosum Business Custom Reports!*\n\n"
            "This bot helps you view detailed transaction reports with revenue breakdown by source.\n\n"
            "Choose an option:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return START_MENU_CODE

    async def handle_start_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle start menu button selections"""
        query = update.callback_query
        await query.answer()

        if query.data == "start_bind":
            return await self._start_bind_flow(update, context)
        elif query.data == "start_list":
            return await self._start_list_flow(update, context)
        elif query.data == "start_menu":
            return await self._start_menu_flow(update, context)
        elif query.data == "start_unbind":
            return await self._start_unbind_flow(update, context)
        elif query.data == "close_conversation":
            await query.edit_message_text("Goodbye! Use /start anytime to access the bot.")
            return ConversationHandler.END
        elif query.data.startswith("unbind_") or query.data == "cancel":
            return await self.handle_unbind_selection(update, context)

        return ConversationHandler.END

    async def _start_bind_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the bind flow from start menu"""
        query = update.callback_query
        context.user_data["command_type"] = "bind_group"

        keyboard = [
            [InlineKeyboardButton("Use Chat ID", callback_data="use_chat_id")],
            [InlineKeyboardButton("Use Group Name", callback_data="use_group_name")],
            [InlineKeyboardButton("Cancel", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "How would you like to search for the group to bind?",
            reply_markup=reply_markup
        )
        return BIND_GROUP_CODE

    async def _start_list_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the list flow from start menu"""
        query = update.callback_query
        private_chat_id = update.effective_chat.id
        bound_groups = self.binding_service.get_bound_groups(private_chat_id)

        if not bound_groups:
            keyboard = [[InlineKeyboardButton("🔗 Bind Group", callback_data="start_bind")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "You have no bound groups.\n\n"
                "Bind groups to view transaction reports.",
                reply_markup=reply_markup
            )
            return START_MENU_CODE

        # Build the list message
        message_lines = [f"📋 Your bound groups ({len(bound_groups)} total):"]
        message_lines.append("")

        for i, group in enumerate(bound_groups, 1):
            group_name = group.group_name or "Unnamed Group"
            group_id = group.chat_id

            # Get package info
            try:
                group_package = await self.group_package_service.get_package_by_chat_id(group.chat_id)
                package_name = group_package.package.value if group_package else "Unknown"
            except Exception:
                package_name = "Unknown"

            message_lines.append(f"{i}. **{group_name}**")
            message_lines.append(f"   • ID: `{group_id}`")
            message_lines.append(f"   • Package: {package_name}")
            message_lines.append("")

        keyboard = [
            [InlineKeyboardButton("📊 View Reports", callback_data="start_menu")],
            [InlineKeyboardButton("🔓 Unbind Group", callback_data="start_unbind")],
            [InlineKeyboardButton("❌ Cancel", callback_data="close_conversation")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "\n".join(message_lines),
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return START_MENU_CODE

    async def _start_menu_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the menu flow from start menu"""
        query = update.callback_query
        private_chat_id = update.effective_chat.id
        bound_groups = self.binding_service.get_bound_groups(private_chat_id)

        if not bound_groups:
            keyboard = [
                [InlineKeyboardButton("🔗 Bind Group", callback_data="start_bind")],
                [InlineKeyboardButton("❌ Cancel", callback_data="close_conversation")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "No groups are bound to this chat. Bind groups first.",
                reply_markup=reply_markup
            )
            return START_MENU_CODE

        # Store bound groups in context
        context.user_data["bound_groups"] = bound_groups

        if len(bound_groups) == 1:
            # Single group - show menu directly
            group = bound_groups[0]
            context.user_data["selected_group"] = group
            return await self._show_report_menu(update, group)
        else:
            # Multiple groups - let user select
            keyboard = []
            for group in bound_groups:
                keyboard.append([InlineKeyboardButton(
                    f"{group.group_name or 'Unnamed'} (ID: {group.chat_id})",
                    callback_data=f"select_{group.id}"
                )])

            keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                "Select a group to view reports:",
                reply_markup=reply_markup
            )
            return MENU_SELECTION_CODE

    async def _start_unbind_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the unbind flow from start menu"""
        query = update.callback_query
        private_chat_id = update.effective_chat.id
        bound_groups = self.binding_service.get_bound_groups(private_chat_id)

        if not bound_groups:
            keyboard = [
                [InlineKeyboardButton("🔗 Bind Group", callback_data="start_bind")],
                [InlineKeyboardButton("❌ Cancel", callback_data="close_conversation")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "No groups are currently bound.",
                reply_markup=reply_markup
            )
            return START_MENU_CODE

        keyboard = []
        for group in bound_groups:
            keyboard.append([InlineKeyboardButton(
                f"Unbind {group.group_name or 'Unnamed'} (ID: {group.chat_id})",
                callback_data=f"unbind_{group.id}"
            )])

        keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "Select a group to unbind:",
            reply_markup=reply_markup
        )
        return START_MENU_CODE

    async def _show_report_menu(self, update: Update, group: Chat):
        """Show report menu for a specific group with breakdown options"""
        group_package = await self.group_package_service.get_package_by_chat_id(group.chat_id)
        package_type = group_package.package if group_package else None

        keyboard = []

        if package_type and package_type.value == 'BUSINESS':
            keyboard.append([InlineKeyboardButton("តាមវេន (Shift)", callback_data="shift_summary")])

        # Daily option
        if package_type and package_type.value in ['TRIAL', 'STANDARD']:
            keyboard.append([InlineKeyboardButton("ប្រចាំថ្ងៃ (Daily)", callback_data="daily_summary")])
        elif package_type and package_type.value in ['BASIC']:
            keyboard.append([InlineKeyboardButton("ប្រចាំថ្ងៃ (Daily)", callback_data="current_date_summary")])

        # Package-based options
        if package_type and package_type.value not in ['BASIC']:
            keyboard.append([InlineKeyboardButton("ប្រចាំសប្តាហ៍ (Weekly)", callback_data="weekly_summary")])
            keyboard.append([InlineKeyboardButton("ប្រចាំខែ (Monthly)", callback_data="monthly_summary")])

        keyboard.append([InlineKeyboardButton("បិទ (Close)", callback_data="close_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        group_name = group.group_name or f"Group {group.chat_id}"
        text = f"📊 *Reports for {group_name}*\nPackage: {package_type.value if package_type else 'Unknown'}\n\nSelect report type (with breakdown):"

        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

        return REPORT_CALLBACK_CODE

    async def handle_bind_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle search method selection for binding"""
        query = update.callback_query
        await query.answer()

        if query.data == "cancel":
            await query.edit_message_text("Binding cancelled.")
            return ConversationHandler.END

        if query.data == "use_chat_id":
            context.user_data["selection_type"] = "chat_id"
            await query.edit_message_text(
                "Please provide the chat ID or group name to search.\n\n"
                "You can search by exact chat ID or partial group name."
            )
        elif query.data == "use_group_name":
            context.user_data["selection_type"] = "group_name"
            await query.edit_message_text(
                "Please provide the group name to search.\n\n"
                "Up to 5 results will be shown."
            )

        return BIND_GROUP_SEARCH_CODE

    async def handle_bind_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle group search input for binding"""
        search_input = update.message.text.strip()
        private_chat_id = update.effective_chat.id

        # Check if it's a numeric chat ID
        if search_input.lstrip('-').isdigit():
            chat_id = int(search_input)
            group = await self.chat_service.get_chat_by_chat_id(chat_id)

            if group:
                # Direct match - bind immediately
                success = self.binding_service.bind_group(private_chat_id, chat_id)

                if success:
                    await update.message.reply_text(
                        f"✅ Successfully bound to group: {group.group_name or chat_id}"
                    )
                else:
                    await update.message.reply_text("❌ Failed to bind group. It may already be bound.")

                return ConversationHandler.END
            else:
                await update.message.reply_text("❌ No group found with that chat ID.")
                return ConversationHandler.END
        else:
            # Search by name
            groups = await self.chat_service.search_chats_by_name(search_input, limit=5)

            if not groups:
                await update.message.reply_text(
                    f"No groups found matching '{search_input}'.\n\nPlease try again or use /start to go back."
                )
                return ConversationHandler.END

            # Show results
            keyboard = []
            for group in groups:
                keyboard.append([InlineKeyboardButton(
                    f"{group.group_name or 'Unnamed'} (ID: {group.chat_id})",
                    callback_data=f"bind_{group.chat_id}"
                )])

            keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"Found {len(groups)} group(s). Select one to bind:",
                reply_markup=reply_markup
            )
            return BIND_GROUP_SELECTION_CODE

    async def handle_bind_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle group selection confirmation for binding"""
        query = update.callback_query
        await query.answer()

        if query.data == "cancel":
            await query.edit_message_text("Binding cancelled.")
            return ConversationHandler.END

        if query.data.startswith("bind_"):
            chat_id = int(query.data.replace("bind_", ""))
            private_chat_id = update.effective_chat.id

            success = self.binding_service.bind_group(private_chat_id, chat_id)

            if success:
                group = await self.chat_service.get_chat_by_chat_id(chat_id)
                await query.edit_message_text(
                    f"✅ Successfully bound to group: {group.group_name or chat_id}"
                )
            else:
                await query.edit_message_text("❌ Failed to bind group. It may already be bound.")

            return ConversationHandler.END

        return ConversationHandler.END

    async def handle_unbind_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle group selection for unbinding"""
        query = update.callback_query
        await query.answer()

        if query.data == "cancel":
            await query.edit_message_text("Unbinding cancelled.")
            return ConversationHandler.END

        if query.data.startswith("unbind_"):
            binding_id = int(query.data.replace("unbind_", ""))

            success = self.binding_service.unbind_group(binding_id)

            if success:
                await query.edit_message_text("✅ Successfully unbound group.")
            else:
                await query.edit_message_text("❌ Failed to unbind group.")

            return ConversationHandler.END

        return ConversationHandler.END

    async def handle_menu_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle group selection from menu"""
        query = update.callback_query
        await query.answer()

        if query.data == "cancel":
            await query.edit_message_text("Cancelled.")
            return ConversationHandler.END

        if query.data.startswith("select_"):
            binding_id = int(query.data.replace("select_", ""))
            bound_groups = context.user_data.get("bound_groups", [])

            selected_group = next((g for g in bound_groups if g.id == binding_id), None)

            if selected_group:
                context.user_data["selected_group"] = selected_group
                return await self._show_report_menu(update, selected_group)

        return ConversationHandler.END

    async def handle_report_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle report generation callbacks - uses custom breakdown"""
        query = update.callback_query
        await query.answer()

        if query.data == "close_menu":
            await query.edit_message_text("Closed.")
            return ConversationHandler.END

        # Get selected group
        selected_group = context.user_data.get("selected_group")
        if not selected_group:
            await query.edit_message_text("Error: No group selected.")
            return ConversationHandler.END

        chat_id = selected_group.chat_id

        # Import here to avoid circular imports
        from services import IncomeService

        income_service = IncomeService()

        try:
            if query.data == "daily_summary" or query.data == "current_date_summary":
                # Get today's income with sources
                incomes = await income_service.get_today_income_with_sources(chat_id)
                title = "Today's Summary"

                if incomes:
                    report = custom_summary_report_with_breakdown(incomes, title)
                    await query.edit_message_text(report, parse_mode="HTML")
                else:
                    await query.edit_message_text("No transactions found for today.")

            elif query.data == "weekly_summary":
                # Get this week's income with sources
                incomes = await income_service.get_weekly_income_with_sources(chat_id)
                title = "This Week's Summary"

                if incomes:
                    report = custom_summary_report_with_breakdown(incomes, title)
                    await query.edit_message_text(report, parse_mode="HTML")
                else:
                    await query.edit_message_text("No transactions found for this week.")

            elif query.data == "monthly_summary":
                # Get this month's income with sources
                incomes = await income_service.get_monthly_income_with_sources(chat_id)
                title = "This Month's Summary"

                if incomes:
                    report = custom_summary_report_with_breakdown(incomes, title)
                    await query.edit_message_text(report, parse_mode="HTML")
                else:
                    await query.edit_message_text("No transactions found for this month.")

            elif query.data == "shift_summary":
                # For shift summary, delegate to menu handler (no breakdown needed for shift-specific reports)
                await self.menu_handler.menu_callback_query_handler(update, context)

        except Exception as e:
            force_log(f"Error in handle_report_callback: {e}", "AutosumBusinessCustomBot", "ERROR")
            await query.edit_message_text(f"Error generating report: {str(e)}")

        return REPORT_CALLBACK_CODE

    def build_app(self) -> Application:
        """Build and configure the bot application"""
        self.app = ApplicationBuilder().token(self.bot_token).build()

        # Main conversation handler
        main_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start_command)],
            states={
                START_MENU_CODE: [
                    CallbackQueryHandler(self.handle_start_menu)
                ],
                BIND_GROUP_CODE: [
                    CallbackQueryHandler(self.handle_bind_selection)
                ],
                BIND_GROUP_SEARCH_CODE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_bind_search)
                ],
                BIND_GROUP_SELECTION_CODE: [
                    CallbackQueryHandler(self.handle_bind_confirmation)
                ],
                MENU_SELECTION_CODE: [
                    CallbackQueryHandler(self.handle_menu_selection)
                ],
                REPORT_CALLBACK_CODE: [
                    CallbackQueryHandler(self.handle_report_callback)
                ],
            },
            fallbacks=[CommandHandler("start", self.start_command)],
            per_message=False,
        )

        self.app.add_handler(main_handler)

        force_log("AutosumBusinessCustomBot application built successfully", "AutosumBusinessCustomBot")
        return self.app

    async def start_polling(self):
        """Start the bot polling (compatible with main_bots_only.py)"""
        if not self.app:
            self.build_app()

        force_log("Starting AutosumBusinessCustomBot polling...", "AutosumBusinessCustomBot")

        # Initialize and start the application
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()

        force_log("AutosumBusinessCustomBot is now running", "AutosumBusinessCustomBot")

        # Keep the task alive (similar to other bots)
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            force_log("AutosumBusinessCustomBot stopping...", "AutosumBusinessCustomBot")
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
            raise
