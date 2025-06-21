import os
import asyncio
import json
from dotenv import load_dotenv
from telethon import TelegramClient, events, Button
from helper.credential_loader import CredentialLoader
from models.income_balance import IncomeService
from models.conversation_tracker import ConversationService
from helper.message_parser import extract_amount_and_currency
from config.database_config import init_db
from handlers.report_handlers import ReportHandler
from datetime import datetime, timedelta
from telethon.events import NewMessage

load_dotenv()


async def start_telegram_bot(bot_token:str):
    # Initialize Telethon bot client
    bot = TelegramClient('bot', int(os.getenv('API_ID')), os.getenv('API_HASH'))
    await bot.start(bot_token=bot_token)
    
    # Initialize the database tables if they don't exist
    try:
        from sqlalchemy import create_engine, inspect
        from models.conversation_tracker import BotQuestion
        
        # First, drop the table if it exists to recreate it with the updated schema
        engine = create_engine(f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}")
        inspector = inspect(engine)
        
        # Check if table exists and drop it to recreate with new schema
        if 'bot_questions' in inspector.get_table_names():
            BotQuestion.__table__.drop(engine)
            
        # Create the table with the new schema
        BotQuestion.__table__.create(engine)
        print("Bot questions table initialized.")
    except Exception as e:
        print(f"Error initializing database tables: {e}")
    
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
        
        # Skip if not a reply to any message
        if not replied_message:
            return
            
        # Check if this is a reply to one of our tracked questions
        chat_id = event.chat_id
        conversation_service = ConversationService()
        question = await conversation_service.get_question_by_message_id(
            chat_id=chat_id,
            message_id=replied_message.id
        )
        
        if question and question.question_type == "date_input":
            # Handle date input response
            await handle_date_input_response(event, question)
            return
    
    try:
        print("Bot is running...")
        await bot.run_until_disconnected()
    except asyncio.CancelledError:
        await bot.disconnect()
        print("Bot stopped by user")

async def start_telethon_client(loader):
    client = TelegramClient('user', int(loader.api_id), loader.api_hash)
    await client.connect()
    await client.start(phone=loader.phone_number)

    @client.on(events.NewMessage(chats=int(loader.chat_id)))
    async def new_message_listener(event):
        currency, amount = extract_amount_and_currency(event.message.text)
        if currency and amount:
            service = IncomeService()
            await service.insert_income(event.chat_id, amount, currency)

    await client.run_until_disconnected()

# Helper functions for handling different callback types
async def handle_main_menu(event, report_handler):
    # Generate menu buttons using Telethon's Button class
    buttons = [
        [Button.inline("ថ្ងៃនេះ", "daily_summary")],
        [Button.inline("ប្រចាំសប្តាហ៍", "weekly_summary")],
        [Button.inline("ប្រចាំខែ", "monthly_summary")]
    ]
    await event.edit("ជ្រើសរើសរបាយការណ៍ប្រចាំ:", buttons=buttons)

async def handle_daily_summary(event, report_handler):
    today = datetime.now()
    buttons = []
    
    # Generate buttons for the last 3 days
    for i in range(2, -1, -1):
        day = today - timedelta(days=i)
        label = day.strftime("%b %d")
        callback_value = day.strftime("%Y-%m-%d")
        buttons.append([Button.inline(label, f"summary_of_{callback_value}")])
    
    # Add additional navigation buttons
    buttons.append([Button.inline("ថ្ងៃផ្សេងទៀត", "other_dates")])
    buttons.append([Button.inline("ត្រឡប់ក្រោយ", "get_menu")])
    
    await event.edit("ឆែករបាយការណ៍ថ្ងៃ:", buttons=buttons)

async def handle_weekly_summary(event, report_handler):
    now = datetime.now()
    year, month = now.year, now.month
    from calendar import monthrange
    last_day = monthrange(year, month)[1]
    
    week_ranges = [(1, 7), (8, 14), (15, 21), (22, last_day)]
    buttons = []
    
    for start_day, end_day in week_ranges:
        start_date = datetime(year, month, start_day)
        end_date = datetime(year, month, min(end_day, last_day))
        label = f"{start_date.strftime('%d %b')} - {end_date.strftime('%d %b')}"
        callback_value = start_date.strftime("%Y-%m-%d")
        buttons.append([Button.inline(label, f"summary_week_{callback_value}")])
    
    buttons.append([Button.inline("ត្រឡប់ក្រោយ", "get_menu")])
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
    
    buttons.append([Button.inline("ត្រឡប់ក្រោយ", "get_menu")])
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
        
        # Acknowledge the button press
        await event.answer(f"Fetching data for {selected_date.strftime('%d %b %Y')}")
        
        # Keep the menu active but indicate selection
        await event.edit(f"Selected: {selected_date.strftime('%d %b %Y')}")
        
        # Send a new message with results
        if not incomes:
            await event.client.send_message(
                chat_id, 
                f"គ្មានប្រតិបត្តិការសម្រាប់ថ្ងៃទី {selected_date.strftime('%d %b %Y')} ទេ។"
            )
            return
        
        message = report_handler.format_totals_message(f"ថ្ងៃទី {selected_date.strftime('%d %b %Y')}", incomes)
        
        # Send results as a new message
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
        
        # Acknowledge the button press
        await event.answer(f"Fetching data for {period_text}")
        
        # Keep the menu active but indicate selection
        await event.edit(f"Selected: {period_text}")
            
        income_service = IncomeService()
        incomes = await income_service.get_income_by_date_and_chat_id(
            chat_id=chat_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Send a new message with results
        if not incomes:
            await event.client.send_message(
                chat_id,
                f"គ្មានប្រតិបត្តិការសម្រាប់ {period_text} ទេ។"
            )
            return
            
        message = report_handler.format_totals_message(period_text, incomes)
        
        # Send results as a new message
        await event.client.send_message(chat_id, message)
        
    except ValueError:
        await event.client.send_message(chat_id, "ទម្រង់កាលបរិច្ឆេទមិនត្រឹមត្រូវ")

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

async def main():
    try:
        # Initialize database
        init_db()
        
        # Load credentials
        loader = CredentialLoader()
        await loader.load_credentials()
        
        # Start both clients
        await asyncio.gather(
            start_telegram_bot(loader.bot_token),
            start_telethon_client(loader)
        )
    except Exception as e:
        print(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user")