"""
Category Management Command Handlers for Telegram Bot

Provides interactive commands for managing sender categories and nicknames.
All operations require admin authorization.

Admin users are defined in config.constants.ADMIN_USERS
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from config.constants import is_admin_user
from helper import force_log
from services.conversation_state_manager import ConversationState, ConversationStateManager
from services.sender_category_service import SenderCategoryService
from services.sender_config_service import SenderConfigService


class CategoryCommandHandler:
    """
    Handler for category management commands.

    Security:
        - All methods require admin authorization
        - Admin users are defined in config.constants.ADMIN_USERS
        - Unauthorized access attempts are logged and denied
    """

    def __init__(self):
        self.conversation_manager = ConversationStateManager()
        self.category_service = SenderCategoryService()
        self.sender_service = SenderConfigService()
        force_log("CategoryCommandHandler initialized", "CategoryCommandHandler")

    # ========== Authorization ==========

    def _check_admin(self, update: Update) -> bool:
        """
        Check if user is authorized to manage categories.

        Args:
            update: Telegram update object

        Returns:
            True if user is admin, False otherwise
        """
        username = update.effective_user.username
        return is_admin_user(username)

    def _get_chat_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Get the chat_id to use for category operations.

        When called from update_group menu, uses the selected_chat_id from context.
        Otherwise, uses the current chat's ID.

        Args:
            update: Telegram update object
            context: Telegram context object

        Returns:
            The chat_id to use for operations
        """
        # Check if there's a selected_chat_id from update_group flow
        selected_chat_id = context.user_data.get("selected_chat_id")
        if selected_chat_id:
            return selected_chat_id

        # Otherwise use the current chat ID
        return update.effective_chat.id

    async def _send_unauthorized_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Send unauthorized access message"""
        username = update.effective_user.username or "Unknown"
        force_log(
            f"Unauthorized category access attempt by user: {username}",
            "CategoryCommandHandler",
            "WARNING",
        )

        message_text = "❌ Unauthorized\n\nOnly admin users can manage categories."

        if update.callback_query:
            await update.callback_query.answer(
                "❌ Unauthorized. Only admins can manage categories.", show_alert=True
            )
        else:
            await update.message.reply_text(message_text)

    # ========== Main Category Menu ==========

    async def show_category_menu(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Show the category management menu"""
        try:
            # Check authorization
            if not self._check_admin(update):
                await self._send_unauthorized_message(update, context)
                return

            keyboard = [
                [InlineKeyboardButton("📋 List Categories", callback_data="category_list")],
                [InlineKeyboardButton("➕ Add Category", callback_data="category_add")],
                [InlineKeyboardButton("✏️ Edit Category", callback_data="category_edit_menu")],
                [InlineKeyboardButton("🗑 Delete Category", callback_data="category_delete")],
                [InlineKeyboardButton("🔗 Assign Senders", callback_data="category_assign")],
                [InlineKeyboardButton("✏️ Set Nickname", callback_data="sender_nickname")],
                [InlineKeyboardButton("❌ Cancel", callback_data="category_cancel")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            message_text = "🏷️ Manage Categories\n\nPlease select an option:"

            # Check if this is a callback query or a command
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    message_text, reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(message_text, reply_markup=reply_markup)

        except Exception as e:
            force_log(
                f"Error in show_category_menu: {e}",
                "CategoryCommandHandler",
                "ERROR",
            )
            import traceback

            force_log(
                f"Traceback: {traceback.format_exc()}",
                "CategoryCommandHandler",
                "ERROR",
            )

    async def handle_callback_query(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle callback queries from inline keyboards"""
        try:
            query = update.callback_query
            callback_data = query.data

            force_log(
                f"Category callback query received: {callback_data}",
                "CategoryCommandHandler",
            )

            # Check authorization for all category operations
            if not self._check_admin(update):
                await self._send_unauthorized_message(update, context)
                return

            # Cancel action
            if callback_data == "category_cancel":
                await query.answer()
                await query.edit_message_text("❌ Cancelled")

            # Category menu entry point (from setup menu)
            elif callback_data == "category_menu":
                await self.show_category_menu(update, context)

            # Back to category menu
            elif callback_data == "category_back":
                await self.show_category_menu(update, context)

            # Category operations
            elif callback_data == "category_list":
                await self.category_list_inline(update, context)
            elif callback_data == "category_add":
                await self.category_add_start_inline(update, context)
            elif callback_data == "category_edit_menu":
                await self.category_edit_menu_inline(update, context)
            elif callback_data == "category_delete":
                await self.category_delete_start_inline(update, context)
            elif callback_data == "category_assign":
                await self.category_assign_start_inline(update, context)
            elif callback_data == "sender_nickname":
                await self.sender_nickname_start_inline(update, context)

            # Cancel conversation callbacks
            elif callback_data in [
                "category_add_cancel",
                "category_delete_cancel",
                "category_edit_cancel",
                "category_assign_cancel",
                "sender_nickname_cancel",
            ]:
                await query.answer()
                user_id = update.effective_user.id
                chat_id = update.effective_chat.id
                self.conversation_manager.end_conversation(chat_id, user_id)
                await self.show_category_menu(update, context)

        except Exception as e:
            force_log(
                f"Error in handle_callback_query: {e}",
                "CategoryCommandHandler",
                "ERROR",
            )
            import traceback

            force_log(
                f"Traceback: {traceback.format_exc()}",
                "CategoryCommandHandler",
                "ERROR",
            )

    # ========== Category List ==========

    async def category_list_inline(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """List all categories (inline version)"""
        try:
            query = update.callback_query
            await query.answer()
            chat_id = self._get_chat_id(update, context)

            # Get all categories
            categories = await self.category_service.list_categories(chat_id)

            if not categories:
                keyboard = [
                    [InlineKeyboardButton("🔙 Back", callback_data="category_back")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "📋 Category List\n\n"
                    "❌ No categories configured yet.\n\n"
                    "Use Add Category to create a category.",
                    reply_markup=reply_markup,
                )
                return

            # Format category list with sender counts
            category_lines = []
            for i, category in enumerate(categories, 1):
                # Get sender count for this category
                senders = await self.category_service.get_senders_by_category(
                    chat_id, category.category_name
                )
                sender_count = len(senders)
                category_lines.append(
                    f"{i}. {category.category_name} ({sender_count} sender{'s' if sender_count != 1 else ''})"
                )

            category_list = "\n".join(category_lines)

            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="category_back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                f"📋 Category List ({len(categories)} total)\n\n{category_list}",
                reply_markup=reply_markup,
            )

        except Exception as e:
            force_log(
                f"Error in category_list_inline: {e}",
                "CategoryCommandHandler",
                "ERROR",
            )

    # ========== Add Category ==========

    async def category_add_start_inline(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Start the add category flow from inline menu"""
        try:
            query = update.callback_query
            await query.answer()
            chat_id = self._get_chat_id(update, context)
            user_id = update.effective_user.id

            # Start conversation
            self.conversation_manager.start_conversation(
                chat_id, user_id, "category_add", ConversationState.WAITING_FOR_NAME
            )

            await query.edit_message_text(
                "➕ Add New Category\n\n"
                "Please reply with the category name:\n\n"
                "Example: VIP Customers"
            )

        except Exception as e:
            force_log(
                f"Error in category_add_start_inline: {e}",
                "CategoryCommandHandler",
                "ERROR",
            )

    async def category_add_handle_name(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle category name input for add category"""
        try:
            chat_id = self._get_chat_id(update, context)
            user_id = update.effective_user.id

            # Check authorization
            if not self._check_admin(update):
                await self._send_unauthorized_message(update, context)
                return

            # Check if user is in this conversation
            state = self.conversation_manager.get_state(chat_id, user_id)
            command = self.conversation_manager.get_command(chat_id, user_id)

            if state != ConversationState.WAITING_FOR_NAME or command != "category_add":
                return

            category_name = update.message.text.strip()

            # Get current max display_order
            categories = await self.category_service.list_categories(chat_id)
            max_order = max([c.display_order for c in categories], default=-1)
            new_order = max_order + 1

            # Create category
            success, message = await self.category_service.create_category(
                chat_id, category_name, new_order
            )

            await update.message.reply_text(message)

            # End conversation
            self.conversation_manager.end_conversation(chat_id, user_id)

        except Exception as e:
            force_log(
                f"Error in category_add_handle_name: {e}",
                "CategoryCommandHandler",
                "ERROR",
            )
            await update.message.reply_text("❌ An error occurred. Please try again.")

    # ========== Edit Category ==========

    async def category_edit_menu_inline(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Show edit category options"""
        try:
            query = update.callback_query
            await query.answer()
            chat_id = self._get_chat_id(update, context)
            user_id = update.effective_user.id

            # Get all categories
            categories = await self.category_service.list_categories(chat_id)

            if not categories:
                keyboard = [
                    [InlineKeyboardButton("🔙 Back", callback_data="category_back")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "❌ No categories configured yet.\n\n"
                    "Use Add Category to create a category first.",
                    reply_markup=reply_markup,
                )
                return

            # Format category list
            category_list = "\n".join(
                [f"• {c.category_name}" for c in categories]
            )

            # Start conversation
            self.conversation_manager.start_conversation(
                chat_id,
                user_id,
                "category_edit",
                ConversationState.WAITING_FOR_NAME,
            )

            await query.edit_message_text(
                f"✏️ Edit Category\n\n"
                f"Current categories:\n{category_list}\n\n"
                f"Please reply with the category name to edit:"
            )

        except Exception as e:
            force_log(
                f"Error in category_edit_menu_inline: {e}",
                "CategoryCommandHandler",
                "ERROR",
            )

    async def category_edit_handle_old_name(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle old category name input for edit"""
        try:
            chat_id = self._get_chat_id(update, context)
            user_id = update.effective_user.id

            # Check authorization
            if not self._check_admin(update):
                await self._send_unauthorized_message(update, context)
                return

            # Check if user is in this conversation
            state = self.conversation_manager.get_state(chat_id, user_id)
            command = self.conversation_manager.get_command(chat_id, user_id)

            if state != ConversationState.WAITING_FOR_NAME or command != "category_edit":
                return

            old_name = update.message.text.strip()

            # Check if category exists
            category = await self.category_service.get_category_by_name(
                chat_id, old_name
            )
            if not category:
                await update.message.reply_text(
                    f"❌ Category '{old_name}' not found.\n\n"
                    "Please try again or send /cancel to cancel."
                )
                return

            # Update conversation state
            self.conversation_manager.update_state(
                chat_id,
                user_id,
                ConversationState.WAITING_FOR_NEW_NAME,
                old_category_name=old_name,
            )

            await update.message.reply_text(
                f"Current name: {old_name}\n\n"
                f"Please reply with the new category name:"
            )

        except Exception as e:
            force_log(
                f"Error in category_edit_handle_old_name: {e}",
                "CategoryCommandHandler",
                "ERROR",
            )
            await update.message.reply_text("❌ An error occurred. Please try again.")

    async def category_edit_handle_new_name(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle new category name input for edit"""
        try:
            chat_id = self._get_chat_id(update, context)
            user_id = update.effective_user.id

            # Check authorization
            if not self._check_admin(update):
                await self._send_unauthorized_message(update, context)
                return

            # Check if user is in this conversation
            state = self.conversation_manager.get_state(chat_id, user_id)
            if state != ConversationState.WAITING_FOR_NEW_NAME:
                return

            # Get conversation data
            data = self.conversation_manager.get_data(chat_id, user_id)
            if not data or "old_category_name" not in data:
                await update.message.reply_text(
                    "❌ Session expired. Please start again."
                )
                self.conversation_manager.end_conversation(chat_id, user_id)
                return

            old_name = data["old_category_name"]
            new_name = update.message.text.strip()

            # Update category
            success, message = await self.category_service.update_category(
                chat_id, old_name, new_category_name=new_name
            )

            await update.message.reply_text(message)

            # End conversation
            self.conversation_manager.end_conversation(chat_id, user_id)

        except Exception as e:
            force_log(
                f"Error in category_edit_handle_new_name: {e}",
                "CategoryCommandHandler",
                "ERROR",
            )
            await update.message.reply_text("❌ An error occurred. Please try again.")

    # ========== Delete Category ==========

    async def category_delete_start_inline(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Start the delete category flow from inline menu"""
        try:
            query = update.callback_query
            await query.answer()
            chat_id = self._get_chat_id(update, context)
            user_id = update.effective_user.id

            # Get all categories
            categories = await self.category_service.list_categories(chat_id)

            if not categories:
                keyboard = [
                    [InlineKeyboardButton("🔙 Back", callback_data="category_back")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "❌ No categories configured yet.\n\n"
                    "Use Add Category to create a category first.",
                    reply_markup=reply_markup,
                )
                return

            # Format category list
            category_list = "\n".join([f"• {c.category_name}" for c in categories])

            # Start conversation
            self.conversation_manager.start_conversation(
                chat_id, user_id, "category_delete", ConversationState.WAITING_FOR_NAME
            )

            await query.edit_message_text(
                f"🗑 Delete Category\n\n"
                f"Current categories:\n{category_list}\n\n"
                f"Please reply with the category name to delete:"
            )

        except Exception as e:
            force_log(
                f"Error in category_delete_start_inline: {e}",
                "CategoryCommandHandler",
                "ERROR",
            )

    async def category_delete_handle_name(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle category name input for delete"""
        try:
            chat_id = self._get_chat_id(update, context)
            user_id = update.effective_user.id

            # Check authorization
            if not self._check_admin(update):
                await self._send_unauthorized_message(update, context)
                return

            # Check if user is in delete conversation
            state = self.conversation_manager.get_state(chat_id, user_id)
            command = self.conversation_manager.get_command(chat_id, user_id)

            if (
                state != ConversationState.WAITING_FOR_NAME
                or command != "category_delete"
            ):
                return

            category_name = update.message.text.strip()

            # Delete category
            success, message = await self.category_service.delete_category(
                chat_id, category_name
            )

            await update.message.reply_text(message)

            # End conversation
            self.conversation_manager.end_conversation(chat_id, user_id)

        except Exception as e:
            force_log(
                f"Error in category_delete_handle_name: {e}",
                "CategoryCommandHandler",
                "ERROR",
            )
            await update.message.reply_text("❌ An error occurred. Please try again.")

    # ========== Assign Senders to Category ==========

    async def category_assign_start_inline(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Start the assign sender to category flow"""
        try:
            query = update.callback_query
            await query.answer()
            chat_id = self._get_chat_id(update, context)
            user_id = update.effective_user.id

            # Get all senders
            senders = await self.sender_service.get_senders(chat_id)

            if not senders:
                keyboard = [
                    [InlineKeyboardButton("🔙 Back", callback_data="category_back")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "❌ No senders configured yet.\n\n"
                    "Use /setup to add senders first.",
                    reply_markup=reply_markup,
                )
                return

            # Format sender list
            sender_list = "\n".join(
                [f"• *{s.sender_account_number} - {s.get_display_name()}" for s in senders]
            )

            # Start conversation
            self.conversation_manager.start_conversation(
                chat_id,
                user_id,
                "category_assign",
                ConversationState.WAITING_FOR_ACCOUNT_NUMBER,
            )

            await query.edit_message_text(
                f"🔗 Assign Sender to Category\n\n"
                f"Current senders:\n{sender_list}\n\n"
                f"Please reply with the account number (last 3 digits):"
            )

        except Exception as e:
            force_log(
                f"Error in category_assign_start_inline: {e}",
                "CategoryCommandHandler",
                "ERROR",
            )

    async def category_assign_handle_account(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle account number input for category assignment"""
        try:
            chat_id = self._get_chat_id(update, context)
            user_id = update.effective_user.id

            # Check authorization
            if not self._check_admin(update):
                await self._send_unauthorized_message(update, context)
                return

            # Check if user is in this conversation
            state = self.conversation_manager.get_state(chat_id, user_id)
            command = self.conversation_manager.get_command(chat_id, user_id)

            if (
                state != ConversationState.WAITING_FOR_ACCOUNT_NUMBER
                or command != "category_assign"
            ):
                return

            account_number = update.message.text.strip()

            # Validate account number
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

            # Get all categories
            categories = await self.category_service.list_categories(chat_id)

            if not categories:
                await update.message.reply_text(
                    "❌ No categories configured yet.\n\n"
                    "Use Add Category to create a category first."
                )
                self.conversation_manager.end_conversation(chat_id, user_id)
                return

            # Format category list
            category_list = "\n".join([f"• {c.category_name}" for c in categories])

            # Update conversation state
            self.conversation_manager.update_state(
                chat_id,
                user_id,
                ConversationState.WAITING_FOR_NAME,
                account_number=account_number,
            )

            await update.message.reply_text(
                f"Sender: {sender.get_display_name()}\n\n"
                f"Available categories:\n{category_list}\n\n"
                f"Please reply with the category name (or 'none' to remove category):"
            )

        except Exception as e:
            force_log(
                f"Error in category_assign_handle_account: {e}",
                "CategoryCommandHandler",
                "ERROR",
            )
            await update.message.reply_text("❌ An error occurred. Please try again.")

    async def category_assign_handle_category(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle category name input for assignment"""
        try:
            chat_id = self._get_chat_id(update, context)
            user_id = update.effective_user.id

            # Check authorization
            if not self._check_admin(update):
                await self._send_unauthorized_message(update, context)
                return

            # Check if user is in this conversation
            state = self.conversation_manager.get_state(chat_id, user_id)
            if state != ConversationState.WAITING_FOR_NAME:
                return

            # Get conversation data
            data = self.conversation_manager.get_data(chat_id, user_id)
            if not data or "account_number" not in data:
                await update.message.reply_text(
                    "❌ Session expired. Please start again."
                )
                self.conversation_manager.end_conversation(chat_id, user_id)
                return

            account_number = data["account_number"]
            category_input = update.message.text.strip()

            # Handle 'none' to remove category
            category_name = None if category_input.lower() == "none" else category_input

            # Assign sender to category
            success, message = await self.category_service.assign_sender_to_category(
                chat_id, account_number, category_name
            )

            await update.message.reply_text(message)

            # End conversation
            self.conversation_manager.end_conversation(chat_id, user_id)

        except Exception as e:
            force_log(
                f"Error in category_assign_handle_category: {e}",
                "CategoryCommandHandler",
                "ERROR",
            )
            await update.message.reply_text("❌ An error occurred. Please try again.")

    # ========== Set Sender Nickname ==========

    async def sender_nickname_start_inline(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Start the set nickname flow"""
        try:
            query = update.callback_query
            await query.answer()
            chat_id = self._get_chat_id(update, context)
            user_id = update.effective_user.id

            # Get all senders
            senders = await self.sender_service.get_senders(chat_id)

            if not senders:
                keyboard = [
                    [InlineKeyboardButton("🔙 Back", callback_data="category_back")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "❌ No senders configured yet.\n\n"
                    "Use /setup to add senders first.",
                    reply_markup=reply_markup,
                )
                return

            # Format sender list
            sender_list = "\n".join(
                [f"• *{s.sender_account_number} - {s.get_display_name()}" for s in senders]
            )

            # Start conversation
            self.conversation_manager.start_conversation(
                chat_id,
                user_id,
                "sender_nickname",
                ConversationState.WAITING_FOR_ACCOUNT_NUMBER,
            )

            await query.edit_message_text(
                f"✏️ Set Sender Nickname\n\n"
                f"Current senders:\n{sender_list}\n\n"
                f"Please reply with the account number (last 3 digits):"
            )

        except Exception as e:
            force_log(
                f"Error in sender_nickname_start_inline: {e}",
                "CategoryCommandHandler",
                "ERROR",
            )

    async def sender_nickname_handle_account(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle account number input for nickname"""
        try:
            chat_id = self._get_chat_id(update, context)
            user_id = update.effective_user.id

            # Check authorization
            if not self._check_admin(update):
                await self._send_unauthorized_message(update, context)
                return

            # Check if user is in this conversation
            state = self.conversation_manager.get_state(chat_id, user_id)
            command = self.conversation_manager.get_command(chat_id, user_id)

            if (
                state != ConversationState.WAITING_FOR_ACCOUNT_NUMBER
                or command != "sender_nickname"
            ):
                return

            account_number = update.message.text.strip()

            # Validate account number
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
                ConversationState.WAITING_FOR_NAME,
                account_number=account_number,
                current_nickname=sender.nickname,
            )

            current_display = sender.get_display_name()
            await update.message.reply_text(
                f"Sender: *{account_number}\n"
                f"Current display: {current_display}\n\n"
                f"Please reply with the new nickname (or 'none' to remove):"
            )

        except Exception as e:
            force_log(
                f"Error in sender_nickname_handle_account: {e}",
                "CategoryCommandHandler",
                "ERROR",
            )
            await update.message.reply_text("❌ An error occurred. Please try again.")

    async def sender_nickname_handle_nickname(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle nickname input"""
        try:
            chat_id = self._get_chat_id(update, context)
            user_id = update.effective_user.id

            # Check authorization
            if not self._check_admin(update):
                await self._send_unauthorized_message(update, context)
                return

            # Check if user is in this conversation
            state = self.conversation_manager.get_state(chat_id, user_id)
            command = self.conversation_manager.get_command(chat_id, user_id)

            if (
                state != ConversationState.WAITING_FOR_NAME
                or command != "sender_nickname"
            ):
                return

            # Get conversation data
            data = self.conversation_manager.get_data(chat_id, user_id)
            if not data or "account_number" not in data:
                await update.message.reply_text(
                    "❌ Session expired. Please start again."
                )
                self.conversation_manager.end_conversation(chat_id, user_id)
                return

            account_number = data["account_number"]
            nickname_input = update.message.text.strip()

            # Handle 'none' to remove nickname
            nickname = None if nickname_input.lower() == "none" else nickname_input

            # Update nickname
            success, message = await self.category_service.update_sender_nickname(
                chat_id, account_number, nickname
            )

            await update.message.reply_text(message)

            # End conversation
            self.conversation_manager.end_conversation(chat_id, user_id)

        except Exception as e:
            force_log(
                f"Error in sender_nickname_handle_nickname: {e}",
                "CategoryCommandHandler",
                "ERROR",
            )
            await update.message.reply_text("❌ An error occurred. Please try again.")

    # ========== Message Router ==========

    async def handle_text_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Route text messages based on conversation state"""
        try:
            chat_id = self._get_chat_id(update, context)
            user_id = update.effective_user.id
            message_text = update.message.text if update.message else ""

            # Check authorization
            if not self._check_admin(update):
                await self._send_unauthorized_message(update, context)
                return

            # Get current state and command
            state = self.conversation_manager.get_state(chat_id, user_id)
            command = self.conversation_manager.get_command(chat_id, user_id)

            # Log for debugging
            force_log(
                f"Category text message received: user={user_id}, chat={chat_id}, state={state}, command={command}, text='{message_text[:50]}'",
                "CategoryCommandHandler",
            )

            if not state or not command:
                return  # Not in a conversation

            # Route based on state and command
            if command == "category_add":
                if state == ConversationState.WAITING_FOR_NAME:
                    await self.category_add_handle_name(update, context)

            elif command == "category_edit":
                if state == ConversationState.WAITING_FOR_NAME:
                    await self.category_edit_handle_old_name(update, context)
                elif state == ConversationState.WAITING_FOR_NEW_NAME:
                    await self.category_edit_handle_new_name(update, context)

            elif command == "category_delete":
                if state == ConversationState.WAITING_FOR_NAME:
                    await self.category_delete_handle_name(update, context)

            elif command == "category_assign":
                if state == ConversationState.WAITING_FOR_ACCOUNT_NUMBER:
                    await self.category_assign_handle_account(update, context)
                elif state == ConversationState.WAITING_FOR_NAME:
                    await self.category_assign_handle_category(update, context)

            elif command == "sender_nickname":
                if state == ConversationState.WAITING_FOR_ACCOUNT_NUMBER:
                    await self.sender_nickname_handle_account(update, context)
                elif state == ConversationState.WAITING_FOR_NAME:
                    await self.sender_nickname_handle_nickname(update, context)

        except Exception as e:
            force_log(
                f"Error in handle_text_message: {e}",
                "CategoryCommandHandler",
                "ERROR",
            )
            import traceback

            force_log(
                f"Traceback: {traceback.format_exc()}",
                "CategoryCommandHandler",
                "ERROR",
            )

    # ========== /cancel Command ==========

    async def cancel_conversation(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Cancel current conversation"""
        try:
            chat_id = self._get_chat_id(update, context)
            user_id = update.effective_user.id

            # Check authorization
            if not self._check_admin(update):
                await self._send_unauthorized_message(update, context)
                return

            # Try to cancel conversation
            cancelled = self.conversation_manager.cancel_conversation(chat_id, user_id)

            if cancelled:
                await update.message.reply_text("❌ Operation cancelled.")
            else:
                await update.message.reply_text("ℹ️ No active operation to cancel.")

        except Exception as e:
            force_log(
                f"Error in cancel_conversation: {e}",
                "CategoryCommandHandler",
                "ERROR",
            )
