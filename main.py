import os
import asyncio
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, MessageHandler, filters
from telethon import TelegramClient, events
from handlers.callback_handlers import menu_callback_handler
from handlers.command_handlers import get_menu_handler
from helper.credential_loader import CredentialLoader
from models.income_balance import IncomeService
from helper.message_parser import extract_amount_and_currency
from handlers.report_handlers import handle_date_input
from config.database_config import init_db

load_dotenv()

async def start_telegram_bot(bot_token:str):
    app = ApplicationBuilder().token(bot_token).build()
    
    app.add_handler(get_menu_handler)
    app.add_handler(menu_callback_handler)  
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_date_input))
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    try:
        while True:
            await asyncio.sleep(1)
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        await app.stop()
        await app.shutdown()
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
    loader = CredentialLoader()
    await loader.load_credentials()
    
    await asyncio.gather(
        start_telegram_bot(loader.bot_token),
        start_telethon_client(loader)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user")