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
    filters,
)

from helper import force_log
from services.handlers.sender_command_handler import SenderCommandHandler

# Get logger
logger = logging.getLogger(__name__)


class SenderManagementBot:
    """
    Dedicated bot for sender management features

    Features:
    - Add/Delete/Update sender configurations
    - List all configured senders
    - Generate daily reports grouped by sender
    - Interactive conversation flows
    """

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.app: Application | None = None
        self.sender_handler = SenderCommandHandler()
        force_log("SenderManagementBot initialized", "SenderManagementBot")

    async def start_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Start command with welcome message"""
        welcome_message = """
👋 Welcome to Sender Management Bot!

This bot helps you manage and track transactions by sender.

📋 **Available Commands:**

**Sender Management:**
• /sender_add - Add new sender
• /sender_delete - Delete sender
• /sender_update - Update sender name
• /sender_list - List all senders

**Reporting:**
• /sender_report - Generate today's report grouped by sender

**Utility:**
• /cancel - Cancel current operation
• /help - Show this help message

🔧 **How to Use:**

1. Add senders using /sender_add
2. Configure their account numbers (last 3 digits)
3. View daily reports with /sender_report

The bot will group all transactions by the configured senders!
        """

        await update.message.reply_text(welcome_message)

    async def help_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Help command"""
        help_message = """
📚 **Sender Management Bot Help**

**Commands:**

**/sender_add** - Add new sender
  Interactive flow to add a sender with:
  - Account number (last 3 digits)
  - Sender name

**/sender_delete** - Delete sender
  Interactive flow to remove a sender

**/sender_update** - Update sender name
  Interactive flow to update an existing sender's name

**/sender_list** - List all senders
  Shows all configured senders for this group

**/sender_report** - Daily sender report
  Generates a report grouped by:
  ✅ Configured senders
  ⚠️ Unknown senders
  ❓ No sender info

**/cancel** - Cancel operation
  Cancels any active interactive flow

**/help** - Show this help

📝 **Example Usage:**

1. Type /sender_add
2. Reply with account number: 708
3. Reply with name: John Doe
4. Done! Sender added.

5. Use /sender_report to see transactions grouped by sender

⚠️ **Note:**
- Account numbers must be exactly 3 digits
- Each sender can only be added once per group
- Conversations timeout after 5 minutes of inactivity
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

        # Sender management commands
        self.app.add_handler(CommandHandler("sender_add", self.sender_handler.sender_add_start))
        self.app.add_handler(CommandHandler("sender_delete", self.sender_handler.sender_delete_start))
        self.app.add_handler(CommandHandler("sender_update", self.sender_handler.sender_update_start))
        self.app.add_handler(CommandHandler("sender_list", self.sender_handler.sender_list))
        self.app.add_handler(CommandHandler("sender_report", self.sender_handler.sender_report))
        self.app.add_handler(CommandHandler("cancel", self.sender_handler.cancel_conversation))

        # Text message handler for conversation states (only in groups, not replies, not commands)
        self.app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & ~filters.REPLY & filters.ChatType.GROUPS,
                self.sender_handler.handle_text_message
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
