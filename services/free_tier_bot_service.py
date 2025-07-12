"""
FreeTierBot is a bot that allows users to register for a free tier of the service.
"""

import logging
from datetime import datetime, timedelta
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import (
    ApplicationBuilder,
    Application,
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from models import IncomeService
from helper.total_summary_report_helper import total_summary_report

logger = logging.getLogger(__name__)


class FreeTierBot:
    """
    FreeTierBot is a bot that allows users to register for a free tier of the service.
    """

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.app: Application | None = None
        self.income_service = IncomeService()
        logger.info("FreeTierBot initialized with token")

    async def start_polling(self) -> None:
        """
        Start polling for new messages.
        """
        if not self.app:
            await self._setup_handlers()

        assert self.app is not None
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()  # type: ignore
        logger.info("FreeTierBot started polling")

    async def _get_menu_buttons(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Get the menu buttons for the event.
        """
        buttons = [
            [InlineKeyboardButton("ប្រចាំថ្ងៃ", callback_data="daily_summary")],
            [InlineKeyboardButton("បិទ", callback_data="close_menu")],
        ]

        await context.bot.send_message(  # type: ignore
            chat_id=int(update.message.chat_id),  # type: ignore
            text="ជ្រើសរើសរបាយការណ៍ប្រចាំ:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    async def get_daily_summary_menu(
        self, update: Update, _: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Get the daily summary menu.
        """
        query = update.callback_query
        chat_id = query.message.chat_id  # type: ignore
        if not chat_id:
            return

        current_date = datetime.now()
        start_date = datetime.strptime(current_date.strftime("%Y-%m-%d"), "%Y-%m-%d")
        end_date = datetime.strptime(
            (current_date + timedelta(days=1)).strftime("%Y-%m-%d"), "%Y-%m-%d"
        )
        incomes = await self.income_service.get_income_by_date_and_chat_id(
            chat_id=chat_id,
            start_date=start_date,
            end_date=end_date,
        )

        if not incomes:
            await query.edit_message_text(  # type: ignore
                f"គ្មានប្រតិបត្តិការសម្រាប់ថ្ងៃទី {current_date.strftime('%d %b %Y')} ទេ។",
            )
            return

        message = total_summary_report(
            incomes, f"ថ្ងៃទី {current_date.strftime('%d %b %Y')}"
        )
        await query.edit_message_text(message)  # type: ignore

    async def _setup_handlers(self) -> None:
        self.app = ApplicationBuilder().token(self.bot_token).build()
        self.app.add_handler(CommandHandler("menu", self._get_menu_buttons))  # type: ignore
        self.app.add_handler(CallbackQueryHandler(self.get_daily_summary_menu, pattern="daily_summary"))  # type: ignore
        self.app.add_handler(CallbackQueryHandler(self.close_menu, pattern="close_menu"))  # type: ignore
        logger.info("FreeTierBot handlers set up")

    async def close_menu(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Close the menu.
        """
        query = update.callback_query
        await query.message.delete()  # type: ignore
        return ConversationHandler.END
