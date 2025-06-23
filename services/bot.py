import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import List, Any

from telethon import TelegramClient, events, Button

from handlers.report_handlers import ReportHandler
from models.chat import ChatService
from models.conversation_tracker import ConversationService
from models.income_balance import IncomeService


async def start_telegram_bot(bot_token: str):
    bot = TelegramClient('bot', int(os.getenv('API_ID')), os.getenv('API_HASH'))
    await bot.start(bot_token=bot_token)

    @bot.on(events.NewMessage(pattern='/menu'))
    async def menu_handler(event):
        buttons = [
            [Button.inline("ប្រចាំថ្ងៃ", "daily_summary")],
            [Button.inline("ប្រចាំសប្តាហ៍", "weekly_summary")],
            [Button.inline("ប្រចាំខែ", "monthly_summary")]
        ]
        await event.respond("ជ្រើសរើសរបាយការណ៍ប្រចាំ:", buttons=buttons)

    @bot.on(events.NewMessage(pattern='/register'))
    async def register_handler(event):
        chat_id = event.chat_id
        chat_service = ChatService()
        success, message = chat_service.register_chat_id(chat_id)
        await event.respond(message)

    @bot.on(events.CallbackQuery())
    async def callback_handler(event):
        data = event.data.decode()
        chat_id = event.chat_id

        report_handler = ReportHandler()

        if data.startswith("summary_week_") or data.startswith("summary_month_"):
            await handle_period_summary(event, report_handler, data)
        else:
            if data == "menu":
                await handle_main_menu(event, report_handler)
            elif data == "daily_summary":
                await handle_daily_summary(event, report_handler)
            elif data == "weekly_summary":
                await handle_weekly_summary(event, report_handler)
            elif data == "monthly_summary":
                await handle_monthly_summary(event, report_handler)
            elif data == "other_dates":
                await handle_other_dates(event, report_handler)
            elif data.startswith("summary_of_"):
                await handle_date_summary(event, report_handler, data)
            else:
                await handle_daily_summary(event, report_handler)

    @bot.on(events.NewMessage())
    async def message_handler(event):
        if event.message.text.startswith('/'):
            return

        replied_message = await event.message.get_reply_message()

        if not replied_message:
            return

        chat_id = event.chat_id
        conversation_service = ConversationService()
        question = await conversation_service.get_question_by_message_id(
            chat_id=chat_id,
            message_id=replied_message.id
        )

        if question and question.question_type == "date_input":
            await handle_date_input_response(event, question)
            return

    try:
        print("Bot is running...")
        await bot.run_until_disconnected()
    except asyncio.CancelledError:
        await bot.disconnect()
        print("Bot stopped by user")


async def handle_date_input_response(event, question):
    try:
        day_str = event.message.text.strip()
        day = int(day_str)

        if day < 1 or day > 31:
            await event.respond("ថ្ងៃមិនត្រឹមត្រូវ។ សូមជ្រើសរើសថ្ងៃពី 1 ដល់ 31។")
            return

        conversation_service = ConversationService()
        context_data = {}
        if question.context_data:
            context_data = json.loads(question.context_data)

        current_month = context_data.get("current_month", datetime.now().strftime("%Y-%m"))
        date_str = f"{current_month}-{day:02d}"

        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d")
            await conversation_service.mark_as_replied(
                chat_id=event.chat_id,
                message_id=question.message_id
            )

            report_handler = ReportHandler()
            income_service = IncomeService()
            incomes = await income_service.get_income_by_date_and_chat_id(
                chat_id=event.chat_id,
                start_date=selected_date,
                end_date=selected_date + timedelta(days=1)
            )

            if not incomes:
                await event.respond(f"គ្មានប្រតិបត្តិការសម្រាប់ថ្ងៃទី {selected_date.strftime('%d %b %Y')} ទេ។")
                return

            message = report_handler.format_totals_message(f"ថ្ងៃទី {selected_date.strftime('%d %b %Y')}", incomes)
            await event.respond(message)

        except ValueError:
            await event.respond("ទម្រង់កាលបរិច្ឆេទមិនត្រឹមត្រូវ")

    except ValueError:
        await event.respond("សូមវាយថ្ងៃជាលេខពី 1 ដល់ 31")
    except Exception as e:
        print(f"Error in handle_date_input_response: {e}")
        await event.respond("មានបញ្ហាក្នុងការដំណើរការសំណើរបស់អ្នក។ សូមព្យាយាមម្តងទៀត។")


async def handle_main_menu(event, report_handler):
    buttons = [
        [Button.inline("ថ្ងៃនេះ", "daily_summary")],
        [Button.inline("ប្រចាំសប្តាហ៍", "weekly_summary")],
        [Button.inline("ប្រចាំខែ", "monthly_summary")]
    ]
    await event.edit("ជ្រើសរើសរបាយការណ៍ប្រចាំ:", buttons=buttons)


async def handle_daily_summary(event, report_handler):
    today = datetime.now()
    buttons = []

    for i in range(2, -1, -1):
        day = today - timedelta(days=i)
        label = day.strftime("%b %d")
        callback_value = day.strftime("%Y-%m-%d")
        buttons.append([Button.inline(label, f"summary_of_{callback_value}")])

    buttons.append([Button.inline("ថ្ងៃផ្សេងទៀត", "other_dates")])
    buttons.append([Button.inline("ត្រឡប់ក្រោយ", "menu")])

    await event.edit("ឆែករបាយការណ៍ថ្ងៃ:", buttons=buttons)


async def handle_weekly_summary(event, report_handler):
    now = datetime.now()
    year, month = now.year, now.month
    from calendar import monthrange
    import calendar
    
    first_day = datetime(year, month, 1)    
    days_to_monday = (first_day.weekday() - 0) % 7
    first_monday = first_day - timedelta(days=days_to_monday)
    
    _, last_day = monthrange(year, month)
    last_date = datetime(year, month, last_day)
    
    buttons = []
    current_monday = first_monday
    
    while current_monday <= last_date:
        sunday = current_monday + timedelta(days=6)
        if current_monday.month != sunday.month:
            label = f"{current_monday.strftime('%d %b')} - {sunday.strftime('%d %b %Y')}"
        else:
            label = f"{current_monday.strftime('%d')} - {sunday.strftime('%d %b %Y')}"
            
        callback_value = current_monday.strftime("%Y-%m-%d")
        buttons.append([Button.inline(label, f"summary_week_{callback_value}")])
        
        current_monday += timedelta(days=7)

    buttons.append([Button.inline("ត្រឡប់ក្រោយ", "menu")])
    await event.edit("ជ្រើសរើសសប្តាហ៍:", buttons=buttons)


async def handle_monthly_summary(event, report_handler):
    now = datetime.now()
    year = now.year
    buttons = []

    for month in range(1, 13):
        month_date = datetime(year, month, 1)
        label = month_date.strftime("%B %Y")
        callback_value = month_date.strftime("%Y-%m")
        buttons.append([Button.inline(label, f"summary_month_{callback_value}")])

    buttons.append([Button.inline("ត្រឡប់ក្រោយ", "menu")])
    await event.edit("ជ្រើសរើសខែ:", buttons=buttons)


async def handle_date_summary(event, report_handler, data):
    chat_id = event.chat_id
    date_str = data.replace("summary_of_", "")

    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d")
        income_service = IncomeService()
        incomes = await income_service.get_income_by_date_and_chat_id(
            chat_id=chat_id,
            start_date=selected_date,
            end_date=selected_date + timedelta(days=1)
        )

        await event.answer(f"Fetching data for {selected_date.strftime('%d %b %Y')}")
        if not incomes:
            await event.client.send_message(
                chat_id,
                f"គ្មានប្រតិបត្តិការសម្រាប់ថ្ងៃទី {selected_date.strftime('%d %b %Y')} ទេ។"
            )
            return

        message = report_handler.format_totals_message(f"ថ្ងៃទី {selected_date.strftime('%d %b %Y')}", incomes)

        await event.client.send_message(chat_id, message)

    except ValueError:
        await event.client.send_message(chat_id, "ទម្រង់កាលបរិច្ឆេទមិនត្រឹមត្រូវ")


async def handle_period_summary(event, report_handler, data):
    chat_id = event.chat_id

    try:
        if data.startswith("summary_week_"):
            start_date = datetime.strptime(data.replace("summary_week_", ""), "%Y-%m-%d")
            end_date = start_date + timedelta(days=7)
            period_text = f"{start_date.strftime('%d')} - {(end_date - timedelta(days=1)).strftime('%d %b %Y')}"
            back_data = "weekly_summary"
        elif data.startswith("summary_month_"):
            start_date = datetime.strptime(data.replace("summary_month_", ""), "%Y-%m")
            from calendar import monthrange
            _, last_day = monthrange(start_date.year, start_date.month)
            end_date = start_date.replace(day=last_day) + timedelta(days=1)
            period_text = start_date.strftime("%B %Y")
            back_data = "monthly_summary"
        else:
            raise ValueError("Invalid period format")

        await event.answer(f"Fetching data for {period_text}")

        income_service = IncomeService()
        incomes = await income_service.get_income_by_date_and_chat_id(
            chat_id=chat_id,
            start_date=start_date,
            end_date=end_date
        )

        if not incomes:
            await event.client.send_message(
                chat_id,
                f"គ្មានប្រតិបត្តិការសម្រាប់ {period_text} ទេ។"
            )
            return

        message = report_handler.format_totals_message(period_text, incomes)

        await event.client.send_message(chat_id, message)

    except ValueError:
        await event.client.send_message(chat_id, "ទម្រង់កាលបរិច្ឆេទមិនត្រឹមត្រូវ")


async def handle_other_dates(event, report_handler):
    chat_id = event.chat_id

    result = await event.client.send_message(
        chat_id,
        "ឆែករបាយការណ៍ថ្ងៃទី:\n\nសូមវាយថ្ងៃ (1-31) ជាការឆ្លើយតបសារនេះដោយប្រើប៊ូតុង 'Reply' ឬ 'ឆ្លើយតប'"
    )

    conversation_service = ConversationService()
    current_month = datetime.now().strftime("%Y-%m")
    context_data = json.dumps({"current_month": current_month})
    await conversation_service.save_question(
        chat_id=chat_id,
        message_id=result.id,
        question_type="date_input",
        context_data=context_data
    )


class ResponseFormatter:
    @staticmethod
    def format_no_data_message(period_text: str) -> str:
        return f"គ្មានប្រតិបត្តិការសម្រាប់ {period_text} ទេ។"
    
    @staticmethod
    def format_date_input_prompt() -> str:
        return "ឆែករបាយការណ៍ថ្ងៃទី:\n\nសូមវាយថ្ងៃ (1-31) ជាការឆ្លើយតបសារនេះដោយប្រើប៊ូតុង 'Reply' ឬ 'ឆ្លើយតប'"
    
    @staticmethod
    def format_invalid_date() -> str:
        return "ទម្រង់កាលបរិច្ឆេទមិនត្រឹមត្រូវ"
