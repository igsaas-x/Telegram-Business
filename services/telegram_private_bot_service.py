from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    Application,
    ConversationHandler,
    CallbackQueryHandler,
)

from helper.logger_utils import force_log
from services.chat_service import ChatService
from services.group_package_service import GroupPackageService
from services.handlers.menu_handler import MenuHandler
from services.private_bot_group_binding_service import PrivateBotGroupBindingService

# Conversation state codes for private bot
BIND_GROUP_CODE = 2001
BIND_GROUP_SELECTION_CODE = 2002
MENU_SELECTION_CODE = 2003
REPORT_CALLBACK_CODE = 2004


class TelegramPrivateBot:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.app: Application | None = None
        self.binding_service = PrivateBotGroupBindingService()
        self.chat_service = ChatService()
        self.group_package_service = GroupPackageService()
        self.menu_handler = MenuHandler()
        
        force_log("TelegramPrivateBot initialized with token", "TelegramPrivateBot")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        await update.message.reply_text(
            "Welcome! This bot helps you view reports from your linked transaction groups.\n\n"
            "Use /bind to link groups with transactions\n"
            "Use /menu to view reports from linked groups\n"
            "Use /unbind to remove group links"
        )

    async def bind_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /bind command to bind groups"""
        context.user_data["command_type"] = "bind_group"
        
        # Get all available groups
        all_groups = self.chat_service.get_all_active_chats()
        
        if not all_groups:
            await update.message.reply_text("No active transaction groups found.")
            return ConversationHandler.END
        
        # Create keyboard with group options
        keyboard = []
        for group in all_groups[:10]:  # Limit to 10 groups for UI clarity
            keyboard.append([InlineKeyboardButton(
                f"{group.group_name or 'Unnamed'} (ID: {group.group_id})",
                callback_data=f"bind_{group.id}"
            )])
        
        keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Select a group to bind:", 
            reply_markup=reply_markup
        )
        return BIND_GROUP_SELECTION_CODE

    async def handle_bind_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle group binding selection"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel":
            await query.edit_message_text("Binding cancelled.")
            return ConversationHandler.END
        
        if query.data.startswith("bind_"):
            group_id = int(query.data.split("_")[1])
            private_chat_id = update.effective_chat.id
            
            try:
                # Bind the group
                self.binding_service.bind_group(private_chat_id, group_id)
                
                # Get group info
                group = self.chat_service.get_chat_by_id(group_id)
                group_name = group.group_name if group else f"Group {group_id}"
                
                await query.edit_message_text(
                    f"Successfully bound to {group_name}!\n\n"
                    "You can now use /menu to view reports from this group."
                )
                
            except Exception as e:
                await query.edit_message_text(f"Error binding group: {str(e)}")
        
        return ConversationHandler.END

    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /menu command"""
        private_chat_id = update.effective_chat.id
        bound_groups = self.binding_service.get_bound_groups(private_chat_id)
        
        if not bound_groups:
            await update.message.reply_text(
                "No groups are bound to this chat. Use /bind to link groups first."
            )
            return ConversationHandler.END
        
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
                    f"{group.group_name or 'Unnamed'} (ID: {group.group_id})",
                    callback_data=f"select_{group.id}"
                )])
            
            keyboard.append([InlineKeyboardButton("All Groups", callback_data="select_all")])
            keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "Select a group to view reports:",
                reply_markup=reply_markup
            )
            return MENU_SELECTION_CODE

    async def _show_report_menu(self, update: Update, group):
        """Show report menu for a specific group"""
        # Get group package to determine available options
        group_package = self.group_package_service.get_group_package_by_chat_id(group.id)
        package_type = group_package.package if group_package else None
        
        keyboard = []
        
        # Always available options
        keyboard.append([InlineKeyboardButton("ប្រចាំថ្ងៃ", callback_data="daily_summary")])
        
        # Package-based options
        if package_type and package_type.value in ['STANDARD', 'PREMIUM']:
            keyboard.append([InlineKeyboardButton("ប្រចាំសប្តាហ៍", callback_data="weekly_summary")])
            keyboard.append([InlineKeyboardButton("ប្រចាំខែ", callback_data="monthly_summary")])
        
        if package_type and package_type.value == 'PREMIUM':
            keyboard.append([InlineKeyboardButton("តាមវេន", callback_data="shift_summary")])
        
        keyboard.append([InlineKeyboardButton("បិទ", callback_data="close_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        group_name = group.group_name or f"Group {group.group_id}"
        text = f"Reports for {group_name}:\nPackage: {package_type.value if package_type else 'Unknown'}\n\nSelect report type:"
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)
        
        return REPORT_CALLBACK_CODE

    async def handle_menu_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle group selection from menu"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel":
            await query.edit_message_text("Menu cancelled.")
            return ConversationHandler.END
        
        bound_groups = context.user_data.get("bound_groups", [])
        
        if query.data == "select_all":
            # Handle multi-group reporting
            context.user_data["selected_groups"] = bound_groups
            keyboard = [
                [InlineKeyboardButton("ប្រចាំថ្ងៃ", callback_data="daily_summary_all")],
                [InlineKeyboardButton("ប្រចាំសប្តាហ៍", callback_data="weekly_summary_all")],
                [InlineKeyboardButton("ប្រចាំខែ", callback_data="monthly_summary_all")],
                [InlineKeyboardButton("បិទ", callback_data="close_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "Combined reports from all bound groups:\n\nSelect report type:",
                reply_markup=reply_markup
            )
            return REPORT_CALLBACK_CODE
        
        elif query.data.startswith("select_"):
            group_id = int(query.data.split("_")[1])
            group = next((g for g in bound_groups if g.id == group_id), None)
            
            if group:
                context.user_data["selected_group"] = group
                return await self._show_report_menu(update, group)
        
        return MENU_SELECTION_CODE

    async def handle_report_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle report generation callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "close_menu":
            await query.edit_message_text("Menu closed.")
            return ConversationHandler.END
        
        # Get the callback data to determine report type
        callback_data = query.data
        private_chat_id = update.effective_chat.id
        
        # Store necessary data for the menu handler
        if "all" in callback_data:
            # Multi-group report
            selected_groups = context.user_data.get("selected_groups", [])
            group_ids = [group.id for group in selected_groups]
            context.user_data["admin_chat_ids"] = group_ids
        else:
            # Single group report
            selected_group = context.user_data.get("selected_group")
            if selected_group:
                context.user_data["admin_chat_id"] = selected_group.id
        
        # Create a pseudo-event similar to the admin bot
        class PseudoCallbackEvent:
            def __init__(self, callback_query, callback_data):
                self.chat_id = callback_query.message.chat_id
                self.data = callback_data.encode("utf-8") if isinstance(callback_data, str) else callback_data
                self.callback_query = True
                self.message = callback_query.message

            async def edit(self, text, buttons=None):
                if buttons:
                    # Convert buttons if needed
                    keyboard = []
                    for row in buttons:
                        keyboard_row = []
                        for button in row:
                            if hasattr(button, "text") and hasattr(button, "data"):
                                button_data = button.data
                                if isinstance(button_data, bytes):
                                    button_data = button_data.decode("utf-8")
                                keyboard_row.append(
                                    InlineKeyboardButton(button.text, callback_data=button_data)
                                )
                        if keyboard_row:
                            keyboard.append(keyboard_row)
                    
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text(text, reply_markup=reply_markup)
                else:
                    await query.edit_message_text(text)

        # Create pseudo-event and call menu handler
        pseudo_event = PseudoCallbackEvent(query, callback_data.replace("_all", ""))
        
        try:
            await self.menu_handler.menu_callback_query_handler(pseudo_event, context)
        except Exception as e:
            await query.edit_message_text(f"Error generating report: {str(e)}")
        
        return REPORT_CALLBACK_CODE

    async def unbind_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /unbind command"""
        private_chat_id = update.effective_chat.id
        bound_groups = self.binding_service.get_bound_groups(private_chat_id)
        
        if not bound_groups:
            await update.message.reply_text("No groups are currently bound.")
            return
        
        keyboard = []
        for group in bound_groups:
            keyboard.append([InlineKeyboardButton(
                f"Unbind {group.group_name or 'Unnamed'} (ID: {group.group_id})",
                callback_data=f"unbind_{group.id}"
            )])
        
        keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Select a group to unbind:",
            reply_markup=reply_markup
        )

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel command"""
        await update.message.reply_text("Operation cancelled.")
        return ConversationHandler.END

    def setup(self):
        """Setup the bot handlers"""
        self.app = ApplicationBuilder().token(self.bot_token).build()

        # Bind conversation handler
        bind_handler = ConversationHandler(
            entry_points=[CommandHandler("bind", self.bind_command)],
            states={
                BIND_GROUP_SELECTION_CODE: [CallbackQueryHandler(self.handle_bind_selection)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_chat=True,
            per_user=True,
        )

        # Menu conversation handler
        menu_handler = ConversationHandler(
            entry_points=[CommandHandler("menu", self.menu_command)],
            states={
                MENU_SELECTION_CODE: [CallbackQueryHandler(self.handle_menu_selection)],
                REPORT_CALLBACK_CODE: [CallbackQueryHandler(self.handle_report_callback)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_chat=True,
            per_user=True,
        )

        # Add handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(bind_handler)
        self.app.add_handler(menu_handler)
        self.app.add_handler(CommandHandler("unbind", self.unbind_command))

        force_log("TelegramPrivateBot handlers set up", "TelegramPrivateBot")

    async def start_polling(self):
        """Start the bot polling"""
        if not self.app:
            self.setup()

        assert self.app is not None
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        force_log("TelegramPrivateBot started polling", "TelegramPrivateBot")