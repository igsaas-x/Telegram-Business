"""
Telegram Sender Management Bot Service

A dedicated bot for managing sender configurations and generating sender reports.
Provides interactive commands for add/delete/update senders and daily reporting.
"""

import logging

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    Application,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from helper import force_log
from services.handlers.category_command_handler import CategoryCommandHandler
from services.handlers.sender_command_handler import SenderCommandHandler

# Get logger
logger = logging.getLogger(__name__)


class SenderManagementBot:
    """
    Dedicated bot for sender management features

    Features:
    - Add/Delete/Update sender configurations
    - Manage sender categories
    - Set sender nicknames
    - List all configured senders
    - Generate daily reports grouped by sender
    - Interactive conversation flows
    """

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.app: Application | None = None
        self.sender_handler = SenderCommandHandler()
        self.category_handler = CategoryCommandHandler()
        force_log("SenderManagementBot initialized", "SenderManagementBot")

    async def start_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Start command with welcome message"""
        welcome_message = """
👋 Welcome to Sender Management Bot!

This bot helps you manage and track transactions by sender.

📋 **Main Commands:**
• /report - View sender reports
• /setup - Configure senders
• /category - Manage categories (Admin only)

**What you can do:**
⚙️ Setup - Add, delete, or list senders
🏷️ Categories - Organize senders by category
✏️ Nicknames - Set custom display names
📊 Reports - View daily, weekly, or monthly reports

🔧 **How to Use:**
1. Type /setup to add senders
2. Add account numbers (last 3 digits) and names
3. Type /category to organize senders (Admin only)
4. Type /report to view reports grouped by sender

The bot will group all transactions by the configured senders!

Type /help for more information.
        """

        await update.message.reply_text(welcome_message)

    async def help_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Help command"""
        help_message = """
📚 **Sender Management Bot Help**

**Main Commands:**
**/report** - View sender reports (Daily, Weekly, Monthly)
**/setup** - Configure senders (Add, Delete, List)
**/category** - Manage categories (Admin only)

**Setup Menu (via /setup):**
  • List Senders - View all configured senders
  • Add Sender - Add a new sender
  • Delete Sender - Remove a sender

**Category Menu (via /category):** [Admin Only]
  • List Categories - View all categories
  • Add Category - Create a new category
  • Edit Category - Update category name
  • Delete Category - Remove a category
  • Assign Senders - Assign senders to categories
  • Set Nickname - Set custom display names

**Reports Menu (via /report):**
  • Daily Report - View today's transactions by sender
  • Weekly Report - View weekly transactions by sender
  • Monthly Report - View monthly transactions by sender

**Other Commands:**
**/start** - Welcome message
**/help** - Show this help
**/cancel** - Cancel current operation

📝 **Example Usage:**

1. Type /setup
2. Click "Add Sender"
3. Reply with account number: 708
4. Reply with account name: John Doe
5. Reply with nickname: Johnny (or skip)
6. Select category
7. Done! Sender added.

8. Type /category (Admin only)
9. Create categories like "VIP", "Delivery Partners"
10. Assign senders to categories
11. Set nicknames for easier identification

12. Type /report
13. Click "Daily Report" to see transactions grouped by category

📊 **Report Features:**
  • Customers - Transactions from unknown/unconfigured senders
  • Category Sections - Transactions grouped by custom categories
  • Nicknames - Shows custom display names if set
  • Summary - Total transactions with working hours

⚠️ **Note:**
- Account numbers must be exactly 3 digits
- Each sender can only be added once per group
- Category management requires admin authorization
- Use the menu buttons to navigate
        """

        await update.message.reply_text(help_message)

    def setup(self):
        """Setup the sender bot with command handlers"""
        if not self.bot_token:
            raise ValueError("Sender bot token is required")

        self.app = ApplicationBuilder().token(self.bot_token).build()

        # Basic commands
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))

        # Main report menu command - shows reports directly
        self.app.add_handler(CommandHandler("report", self.sender_handler.show_sender_menu))

        # Setup command for sender configuration
        self.app.add_handler(CommandHandler("setup", self.sender_handler.show_setup_menu))

        # Category management command (admin only)
        self.app.add_handler(CommandHandler("category", self.category_handler.show_category_menu))

        # Keep old commands for backward compatibility (optional - can remove later)
        self.app.add_handler(CommandHandler("sender_add", self.sender_handler.sender_add_start))
        self.app.add_handler(CommandHandler("sender_delete", self.sender_handler.sender_delete_start))
        self.app.add_handler(CommandHandler("sender_update", self.sender_handler.sender_update_start))
        self.app.add_handler(CommandHandler("sender_list", self.sender_handler.sender_list))
        self.app.add_handler(CommandHandler("sender_report", self.sender_handler.sender_report))

        # Cancel command - shared by both handlers
        async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            """Universal cancel handler for all conversations"""
            # Try sender handler first
            await self.sender_handler.cancel_conversation(update, context)
            # Also try category handler in case there's a category conversation
            await self.category_handler.cancel_conversation(update, context)

        self.app.add_handler(CommandHandler("cancel", cancel_handler))

        # Callback query handlers for inline keyboard buttons
        # Category callbacks (priority for category-related callbacks)
        self.app.add_handler(
            CallbackQueryHandler(
                self.category_handler.handle_callback_query,
                pattern="^category_"
            )
        )
        # Sender callbacks (for all other callbacks)
        self.app.add_handler(CallbackQueryHandler(self.sender_handler.handle_callback_query))

        # Text message handler for conversation states
        # Route messages to both handlers (they will check if they have an active conversation)
        async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            """Route text messages to appropriate handler based on conversation state"""
            # Try category handler first (it will check if it has an active conversation)
            await self.category_handler.handle_text_message(update, context)
            # Also try sender handler (it will check if it has an active conversation)
            await self.sender_handler.handle_text_message(update, context)

        self.app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                text_router
            )
        )

        # Error handler
        self.app.add_error_handler(self.error_handler)

        force_log("SenderManagementBot setup completed", "SenderManagementBot")

    async def error_handler(
        self, update: object, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle errors in the sender bot"""
        force_log(f"Sender bot error: {context.error}", "SenderManagementBot", "ERROR")

        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An error occurred. Please try again or use /help for assistance."
            )

    async def start_polling(self):
        """Start the sender bot polling"""
        try:
            self.setup()
            force_log("Starting SenderManagementBot polling...", "SenderManagementBot")
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling()
            force_log("SenderManagementBot polling started successfully", "SenderManagementBot")
        except Exception as e:
            force_log(f"Error starting SenderManagementBot polling: {e}", "SenderManagementBot", "ERROR")
            raise

    async def stop(self):
        """Stop the sender bot"""
        try:
            if self.app:
                force_log("Stopping SenderManagementBot...", "SenderManagementBot")
                await self.app.updater.stop()
                await self.app.stop()
                await self.app.shutdown()
                force_log("SenderManagementBot stopped successfully", "SenderManagementBot")
        except Exception as e:
            force_log(f"Error stopping SenderManagementBot: {e}", "SenderManagementBot", "ERROR")

    def run(self):
        """Run the sender bot (blocking)"""
        try:
            self.setup()
            force_log("Running SenderManagementBot...", "SenderManagementBot")
            self.app.run_polling()
        except KeyboardInterrupt:
            force_log("SenderManagementBot stopped by user", "SenderManagementBot")
        except Exception as e:
            force_log(f"Error running SenderManagementBot: {e}", "SenderManagementBot", "ERROR")
            raise
