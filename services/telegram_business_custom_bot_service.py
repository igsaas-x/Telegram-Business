import asyncio
import logging

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    Application,
)

from helper import force_log
from services import IncomeService

# Get logger
logger = logging.getLogger(__name__)


class AutosumBusinessCustomBot:
    """
    Custom business bot for viewing summary reports with revenue breakdown
    """

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.app: Application | None = None
        self.income_service = IncomeService()
        force_log("AutosumBusinessCustomBot initialized with token", "AutosumBusinessCustomBot")

    async def custom_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Custom bot start command"""
        welcome_message = """
🏢 Welcome to Autosum Business Custom Reports!

This bot displays revenue summaries with detailed breakdown by payment source.

📊 Available Commands:
• /summary_today - Today's revenue with breakdown
• /summary_week - This week's revenue with breakdown
• /summary_month - This month's revenue with breakdown

💡 The breakdown shows revenue by source:
   - Cash
   - Bank Card
   - Ctrip
   - Agoda
   - WeChat
   - Alipay
   - And more...
        """
        await update.message.reply_text(welcome_message)

    async def summary_today(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Show today's summary with revenue breakdown"""
        chat_id = update.effective_chat.id

        try:
            # Get today's income with revenue sources loaded
            incomes = await self.income_service.get_today_income_with_sources(chat_id)

            if not incomes:
                await update.message.reply_text("No transactions found for today.")
                return

            # Generate report with breakdown
            from helper.custom_summary_report_helper import custom_summary_report_with_breakdown
            report = custom_summary_report_with_breakdown(incomes, "Today's Summary")

            await update.message.reply_text(report, parse_mode="HTML")

        except Exception as e:
            force_log(f"Error in summary_today: {e}", "AutosumBusinessCustomBot", "ERROR")
            await update.message.reply_text("Error generating summary report.")

    async def summary_week(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Show this week's summary with revenue breakdown"""
        chat_id = update.effective_chat.id

        try:
            # Get this week's income with revenue sources loaded
            incomes = await self.income_service.get_weekly_income_with_sources(chat_id)

            if not incomes:
                await update.message.reply_text("No transactions found for this week.")
                return

            # Generate report with breakdown
            from helper.custom_summary_report_helper import custom_summary_report_with_breakdown
            report = custom_summary_report_with_breakdown(incomes, "This Week's Summary")

            await update.message.reply_text(report, parse_mode="HTML")

        except Exception as e:
            force_log(f"Error in summary_week: {e}", "AutosumBusinessCustomBot", "ERROR")
            await update.message.reply_text("Error generating summary report.")

    async def summary_month(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Show this month's summary with revenue breakdown"""
        chat_id = update.effective_chat.id

        try:
            # Get this month's income with revenue sources loaded
            incomes = await self.income_service.get_monthly_income_with_sources(chat_id)

            if not incomes:
                await update.message.reply_text("No transactions found for this month.")
                return

            # Generate report with breakdown
            from helper.custom_summary_report_helper import custom_summary_report_with_breakdown
            report = custom_summary_report_with_breakdown(incomes, "This Month's Summary")

            await update.message.reply_text(report, parse_mode="HTML")

        except Exception as e:
            force_log(f"Error in summary_month: {e}", "AutosumBusinessCustomBot", "ERROR")
            await update.message.reply_text("Error generating summary report.")

    def build_app(self) -> Application:
        """Build and configure the bot application"""
        self.app = ApplicationBuilder().token(self.bot_token).build()

        # Add command handlers
        self.app.add_handler(CommandHandler("start", self.custom_start))
        self.app.add_handler(CommandHandler("summary_today", self.summary_today))
        self.app.add_handler(CommandHandler("summary_week", self.summary_week))
        self.app.add_handler(CommandHandler("summary_month", self.summary_month))

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
