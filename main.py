import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient, events, Button
from helper.credential_loader import CredentialLoader
from models.income_balance import IncomeService
from helper.message_parser import extract_amount_and_currency
from config.database_config import init_db
from handlers.report_handlers import ReportHandler
from datetime import datetime, timedelta

load_dotenv()


async def start_telegram_bot(bot_token:str):
    # Initialize Telethon bot client
    bot = TelegramClient('bot', int(os.getenv('API_ID')), os.getenv('API_HASH'))
    await bot.start(bot_token=bot_token)
    
    @bot.on(events.NewMessage(pattern='/get_menu'))
    async def get_menu_handler(event):
        # Simple menu using Telethon's Button
        buttons = [
            [Button.inline("ថ្ងៃនេះ", "daily_summary")],
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
    # Send a new message prompting for the date
    await event.client.send_message(
        event.chat_id,
        "ឆែករបាយការណ៍ថ្ងៃទី: សូមវាយថ្ងៃ (1-31)"
    )
    
    # Keep the menu with an acknowledgment of the selection
    await event.edit("Selected: ថ្ងៃផ្សេងទៀត")
    
    # Note: For a complete implementation, you would need to handle text responses differently
    # This would require additional event handlers for NewMessage events

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