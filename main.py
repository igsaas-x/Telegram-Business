import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient, events, Button
from helper.credential_loader import CredentialLoader
from models.income_balance import IncomeService
from helper.message_parser import extract_amount_and_currency
from config.database_config import init_db

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
        # Simple acknowledgment of button press
        data = event.data.decode()
        await event.answer(f"Selected: {data}")
        # Additional handling could be implemented here
    
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