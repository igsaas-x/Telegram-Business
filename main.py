import asyncio
import os

from config import load_environment, CURRENT_ENV
from telethon import TelegramClient, events

from config.database_config import create_db_tables
from helper.credential_loader import CredentialLoader
from helper.message_parser import extract_amount_and_currency
from models.chat import ChatService
from models.income_balance import IncomeService
from services.bot import start_telegram_bot

load_environment()

async def start_telethon_client(loader):
    client = TelegramClient('user', int(loader.api_id), loader.api_hash)
    await client.connect()
    await client.start(phone=loader.phone_number)

    chat_service = ChatService()

    @client.on(events.NewMessage)
    async def new_message_listener(event):
        chat_ids = chat_service.get_all_chat_ids()
        if event.chat_id not in chat_ids:
            return
        currency, amount = extract_amount_and_currency(event.message.text)
        print(currency, amount)
        if currency and amount:
            service = IncomeService()
            await service.insert_income(event.chat_id, amount, currency)

    await client.run_until_disconnected()

async def main():
    try:
        # Initialize database
        create_db_tables()
        
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