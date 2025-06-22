import os
import asyncio
import json
from telethon import TelegramClient, events, Button
from models.income_balance import IncomeService
from models.conversation_tracker import ConversationService
from handlers.report_handlers import ReportHandler
from datetime import datetime, timedelta


async def start_telegram_bot(bot_token:str):
    # Initialize Telethon bot client
    bot = TelegramClient('bot', int(os.getenv('API_ID')), os.getenv('API_HASH'))
    await bot.start(bot_token=bot_token)
    
    # Initialize the database tables if they don't exist
    try:
        from sqlalchemy import create_engine, inspect
        from models.conversation_tracker import BotQuestion
        from models.income_balance import IncomeBalance
        
        # First, drop the tables if they exist to recreate them with the updated schema
        engine = create_engine(f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}")
        inspector = inspect(engine)
        
        # Check if tables exist and drop them to recreate with new schema
        if 'bot_questions' in inspector.get_table_names():
            BotQuestion.__table__.drop(engine)
            
        if 'income_balance' in inspector.get_table_names():
            IncomeBalance.__table__.drop(engine)
            
        # Create the tables with the new schema
        BotQuestion.__table__.create(engine)
        IncomeBalance.__table__.create(engine)
        print("Database tables initialized.")
    except Exception as e:
        print(f"Error initializing database tables: {e}")
        # Don't raise the exception to allow the bot to start even if table creation fails
        # The user can manually fix the database issues
    
    @bot.on(events.NewMessage(pattern='/get_menu'))
    async def get_menu_handler(event):
        # Simple menu using Telethon's Button
        buttons = [
            [Button.inline("ប្រចាំថ្ងៃ", "daily_summary")],
            [Button.inline("ប្រចាំសប្តាហ៍", "weekly_summary")],
            [Button.inline("ប្រចាំខែ", "monthly_summary")]
        ]
        await event.respond("ជ្រើសរើសរបាយការណ៍ប្រចាំ:", buttons=buttons)

    @bot.on(events.CallbackQuery())
    async def callback_handler(event):
        data = event.data.decode()
        chat_id = event.chat_id
        
        # Create report handler
        report_handler = ReportHandler()
        
        # Handle different callback types based on the data pattern
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
                
    # Handler for text responses
    @bot.on(events.NewMessage())
    async def message_handler(event):
        # Ignore command messages
        if event.message.text.startswith('/'):
            return
            
        # Only process replies to messages
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
                # Add other question type handlers here if needed
                
    try:
        print("Bot is running...")
        await bot.run_until_disconnected()
    finally:
        print("--- start_telegram_bot() finished ---")
        await bot.disconnect()

async def handle_main_menu(event, report_handler):
    buttons = [
        [Button.inline("ប្រចាំថ្ងៃ", "daily_summary")],
        [Button.inline("ប្រចាំសប្តាហ៍", "weekly_summary")],
        [Button.inline("ប្រចាំខែ", "monthly_summary")],
        [Button.inline("ថ្ងៃផ្សេងទៀត", "other_dates")]
    ]
    await event.edit("ជ្រើសរើសរបាយការណ៍ប្រចាំ:", buttons=buttons)

async def handle_daily_summary(event, report_handler):
    today = datetime.now()
    income_service = IncomeService()
    incomes = await income_service.get_income_by_date_and_chat_id(
        chat_id=event.chat_id,
        start_date=today,
        end_date=today + timedelta(days=1)
    )
    
    if not incomes:
        await event.edit(f"គ្មានប្រតិបត្តិការសម្រាប់ថ្ងៃទី {today.strftime('%d %b %Y')} ទេ។")
        return
    
    message = report_handler.format_totals_message(f"សរុបប្រចាំថ្ងៃ ({today.strftime('%d %b %Y')})", incomes)
    await event.edit(message)

async def handle_weekly_summary(event, report_handler):
    today = datetime.now()
    
    # Calculate the start and end of the current week (assuming Monday is the first day)
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    income_service = IncomeService()
    incomes = await income_service.get_income_by_date_and_chat_id(
        chat_id=event.chat_id,
        start_date=start_of_week,
        end_date=end_of_week + timedelta(days=1)
    )
    
    if not incomes:
        await event.edit(f"គ្មានប្រតិបត្តិការសម្រាប់សប្តាហ៍នេះ ({start_of_week.strftime('%d %b')} - {end_of_week.strftime('%d %b %Y')}) ទេ។")
        return
        
    message = report_handler.format_totals_message(f"សរុបប្រចាំសប្តាហ៍ ({start_of_week.strftime('%d %b')} - {end_of_week.strftime('%d %b %Y')})", incomes)
    await event.edit(message)

async def handle_monthly_summary(event, report_handler):
    today = datetime.now()
    income_service = IncomeService()
    incomes = await income_service.get_income_by_month_and_chat_id(
        chat_id=event.chat_id, 
        month=today.month, 
        year=today.year
    )
    
    if not incomes:
        await event.edit(f"គ្មានប្រតិបត្តិការសម្រាប់ខែ {today.strftime('%B %Y')} ទេ។")
        return
        
    message = report_handler.format_totals_message(f"សរុបប្រចាំខែ ({today.strftime('%B %Y')})", incomes)
    await event.edit(message)

async def handle_date_summary(event, report_handler, data):
    # Extract date from callback data (e.g., 'summary_of_2023-10-25')
    date_str = data.replace("summary_of_", "")
    selected_date = datetime.strptime(date_str, "%Y-%m-%d")
    
    income_service = IncomeService()
    incomes = await income_service.get_income_by_date_and_chat_id(
        chat_id=event.chat_id,
        start_date=selected_date,
        end_date=selected_date + timedelta(days=1)
    )
    
    if not incomes:
        await event.edit(f"គ្មានប្រតិបត្តិការសម្រាប់ថ្ងៃទី {selected_date.strftime('%d %b %Y')} ទេ។")
        return
    
    message = report_handler.format_totals_message(f"សរុបសម្រាប់ថ្ងៃទី {selected_date.strftime('%d %b %Y')}", incomes)
    await event.edit(message)

async def handle_period_summary(event, report_handler, data):
    # Handles summaries for specific weeks or months
    period_type, year, value = data.replace("summary_", "").split('_')
    year = int(year)
    value = int(value)
    
    income_service = IncomeService()
    
    if period_type == "week":
        # Calculate start and end dates for the selected week
        start_of_year = datetime(year, 1, 1)
        start_of_week = start_of_year + timedelta(weeks=value - 1, days=-start_of_year.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        incomes = await income_service.get_income_by_date_and_chat_id(
            chat_id=event.chat_id,
            start_date=start_of_week,
            end_date=end_of_week + timedelta(days=1)
        )
        
        period_str = f"សប្តាហ៍ទី {value} ({start_of_week.strftime('%d %b')} - {end_of_week.strftime('%d %b %Y')})"
        
    elif period_type == "month":
        incomes = await income_service.get_income_by_month_and_chat_id(
            chat_id=event.chat_id, 
            month=value, 
            year=year
        )
        
        month_name = datetime(year, value, 1).strftime('%B')
        period_str = f"ខែ {month_name} {year}"
        
    else:
        await event.edit("Invalid period type.")
        return

    if not incomes:
        await event.edit(f"គ្មានប្រតិបត្តិការសម្រាប់ {period_str} ទេ។")
        return
    
    message = report_handler.format_totals_message(f"សរុបសម្រាប់ {period_str}", incomes)
    await event.edit(message)

async def handle_other_dates(event, report_handler):
    chat_id = event.chat_id
    
    # Send a new message prompting for the date, clearly indicating to reply to this message
    result = await event.client.send_message(
        chat_id,
        "ឆែករបាយការណ៍ថ្ងៃទី:\n\nសូមវាយថ្ងៃ (1-31) ជាការឆ្លើយតបសារនេះដោយប្រើប៊ូតុង 'Reply' ឬ 'ឆ្លើយតប'"
    )
    
    # Keep the menu with an acknowledgment of the selection
    await event.edit("Selected: ថ្ងៃផ្សេងទៀត")
    
    # Save this question in our tracking database
    conversation_service = ConversationService()
    current_month = datetime.now().strftime("%Y-%m")
    context_data = json.dumps({"current_month": current_month})
    await conversation_service.save_question(
        chat_id=chat_id,
        message_id=result.id,  # Store the message_id of our question
        question_type="date_input",
        context_data=context_data
    )

async def handle_date_input_response(event, question):
    """Handle a response to a date input question"""
    try:
        # Get the day number from the message text
        day_str = event.message.text.strip()
        day = int(day_str)
        
        if day < 1 or day > 31:
            await event.respond("ថ្ងៃមិនត្រឹមត្រូវ។ សូមជ្រើសរើសថ្ងៃពី 1 ដល់ 31។")
            return
        
        # Get the current month from the question context
        conversation_service = ConversationService()
        context_data = {}
        if question.context_data:
            context_data = json.loads(question.context_data)
            
        current_month = context_data.get("current_month", datetime.now().strftime("%Y-%m"))
        date_str = f"{current_month}-{day:02d}"
        
        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            # Mark the question as replied
            await conversation_service.mark_as_replied(
                chat_id=event.chat_id,
                message_id=question.message_id
            )
            
            # Get income data
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
