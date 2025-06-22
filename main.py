import asyncio

from dotenv import load_dotenv
from telethon import TelegramClient, events

from config.database_config import init_db
from helper.credential_loader import CredentialLoader
from helper.message_parser import extract_amount_and_currency
from models.income_balance import IncomeService
from services.bot import start_telegram_bot

load_dotenv()

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