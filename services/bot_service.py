import os
import json
from telethon import TelegramClient, events, Button
from models.income_balance import IncomeService
from models.conversation_tracker import ConversationService
from handlers.report_handlers import ReportHandler
from datetime import datetime, timedelta
from database import initialize_database, add_chat_id
from telethon.events import NewMessage

async def handle_main_menu(event, report_handler):
    # Main menu handler
    buttons = [
        [Button.inline("ប្រចាំថ្ងៃ", "daily_summary")],
        [Button.inline("ប្រចាំសប្តាហ៍", "weekly_summary")],
        [Button.inline("ប្រចាំខែ", "monthly_summary")]
    ]
    await event.respond("ជ្រើសរើសរបាយការណ៍ប្រចាំ:", buttons=buttons)

async def handle_daily_summary(event, report_handler):
    # Daily summary handler
    today = datetime.now()
    income_service = IncomeService()
    incomes = await income_service.get_income_by_date_and_chat_id(
        chat_id=event.chat_id,
        start_date=today.replace(hour=0, minute=0, second=0, microsecond=0),
        end_date=today.replace(hour=23, minute=59, second=59, microsecond=999999)
    )
    message = report_handler.format_totals_message(f"សរុបប្រចាំថ្ងៃ ({today.strftime('%d %b %Y')})", incomes)
    await event.respond(message)

async def handle_weekly_summary(event, report_handler):
    # Weekly summary handler
    today = datetime.now()
    buttons = []
    for i in range(4):
        start_of_week = today - timedelta(days=today.weekday() + (i * 7))
        end_of_week = start_of_week + timedelta(days=6)
        
        # Format the button text
        button_text = f"{start_of_week.strftime('%d %b')} - {end_of_week.strftime('%d %b %Y')}"
        
        # Create the callback data
        callback_data = f"summary_week_{start_of_week.strftime('%Y-%m-%d')}_{end_of_week.strftime('%Y-%m-%d')}"
        
        buttons.append([Button.inline(button_text, callback_data)])
        
    await event.respond("ជ្រើសរើសសប្តាហ៍:", buttons=buttons)

async def handle_monthly_summary(event, report_handler):
    # Monthly summary handler
    today = datetime.now()
    buttons = []
    for i in range(4):
        month = today.month - i
        year = today.year
        if month <= 0:
            month += 12
            year -= 1
        
        month_name = datetime(year, month, 1).strftime("%B %Y")
        callback_data = f"summary_month_{year}-{month:02d}"
        buttons.append([Button.inline(month_name, callback_data)])
        
    await event.respond("ជ្រើសរើសខែ:", buttons=buttons)

async def handle_date_summary(event, report_handler, data):
    # Date summary handler
    date_str = data.split("_")[-1]
    selected_date = datetime.strptime(date_str, "%Y-%m-%d")
    
    income_service = IncomeService()
    incomes = await income_service.get_income_by_date_and_chat_id(
        chat_id=event.chat_id,
        start_date=selected_date.replace(hour=0, minute=0, second=0, microsecond=0),
        end_date=selected_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    )
    
    message = report_handler.format_totals_message(f"សរុបសម្រាប់ {selected_date.strftime('%d %b %Y')}", incomes)
    await event.respond(message)

async def handle_period_summary(event, report_handler, data):
    # Period summary handler
    parts = data.split("_")
    period_type = parts[1]
    
    if period_type == "week":
        start_date_str = parts[2]
        end_date_str = parts[3]
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        title = f"សរុបប្រចាំសប្តាហ៍ ({start_date.strftime('%d %b')} - {end_date.strftime('%d %b %Y')})"
    elif period_type == "month":
        year, month = map(int, parts[2].split("-"))
        start_date = datetime(year, month, 1)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        title = f"សរុបប្រចាំខែ {start_date.strftime('%B %Y')}"
    else:
        await event.respond("Invalid period type.")
        return

    income_service = IncomeService()
    incomes = await income_service.get_income_by_date_and_chat_id(
        chat_id=event.chat_id,
        start_date=start_date,
        end_date=end_date
    )
    
    message = report_handler.format_totals_message(title, incomes)
    await event.respond(message)

async def handle_other_dates(event, report_handler):
    # Other dates handler
    chat_id = event.chat_id
    result = await event.client.send_message(
        chat_id,
        "ឆែករបាយការណ៍ថ្ងៃទី:\n\nសូមវាយថ្ងៃ (1-31) ជាការឆ្លើយតបសារនេះដោយប្រើប៊ូតុង 'Reply' ឬ 'ឆ្លើយតប'"
    )
    await event.edit("Selected: ថ្ងៃផ្សេងទៀត")
    conversation_service = ConversationService()
    current_month = datetime.now().strftime("%Y-%m")
    context_data = json.dumps({"current_month": current_month})
    await conversation_service.save_question(
        chat_id=chat_id,
        message_id=result.id,
        question_type="date_input",
        context_data=context_data
    )

async def handle_date_input_response(event, question):
    # Date input response handler
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

async def start_telegram_bot(bot_token: str):
    bot = TelegramClient('bot', int(os.getenv('API_ID')), os.getenv('API_HASH'))
    await bot.start(bot_token=bot_token)

    initialize_database()

    @bot.on(events.NewMessage(pattern='/register'))
    async def register_handler(event):
        chat_id = event.chat_id
        add_chat_id(chat_id)
        await event.respond('You have been registered to receive notifications.')

    @bot.on(events.NewMessage(pattern='/get_menu'))
    async def get_menu_handler(event):
        await handle_main_menu(event, ReportHandler())

    @bot.on(events.CallbackQuery())
    async def callback_handler(event):
        data = event.data.decode()
        report_handler = ReportHandler()
        
        if data.startswith("summary_week_") or data.startswith("summary_month_"):
            await handle_period_summary(event, report_handler, data)
        else:
            if data == "get_menu":
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
        if replied_message:
            conversation_service = ConversationService()
            question = await conversation_service.get_question_by_message_id(
                chat_id=event.chat_id,
                message_id=replied_message.id
            )
            
            if question and not question.is_replied:
                if question.question_type == "date_input":
                    await handle_date_input_response(event, question)

    print("Bot is running...")
    await bot.run_until_disconnected()