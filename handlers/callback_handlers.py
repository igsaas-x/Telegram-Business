from telegram.ext import CallbackQueryHandler, CommandHandler
from handlers.report_handlers import ReportHandler

report_handler = ReportHandler()
async def handle_menu_click(update, context):
    query = update.callback_query
    data = query.data or ""

    if data.startswith("summary_week_") or data.startswith("summary_month_"):
        await report_handler.handle_period_summary(update, context)
    else:
        match data:
            case "get_menu":
                await report_handler.handle_main_menu(update, context)
            case "daily_summary":
                await report_handler.handle_daily_summary(update, context)
            case "weekly_summary":
                await report_handler.handle_weekly_summary(update, context)
            case "monthly_summary":
                await report_handler.handle_monthly_summary(update, context)
            case "other_dates":
                await report_handler.handle_other_dates(update, context)
            case d if d and d.startswith("summary_of_"):
                await report_handler.handle_date_summary(update, context)
            case _:
                await report_handler.handle_daily_summary(update, context)

menu_callback_handler = CallbackQueryHandler(
    handle_menu_click,
    pattern=(
        r"^(get_menu|daily_summary|weekly_summary|monthly_summary|"
        r"other_dates|"
        r"summary_of_\d{4}-\d{2}-\d{2}|"
        r"summary_week_\d{4}-\d{2}-\d{2}|"
        r"summary_month_\d{4}-\d{2})$"
    )
)
