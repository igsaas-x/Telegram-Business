import asyncio
print("--- main.py starting ---")
from dotenv import load_dotenv
from telethon import TelegramClient, events
from helper.credential_loader import CredentialLoader
from models.income_balance import IncomeService
from helper.message_parser import extract_amount_and_currency
from config.database_config import init_db
from services.bot import start_telegram_bot

load_dotenv()


async def start_telethon_client(loader):
    print("--- start_telethon_client() starting ---")
    client = TelegramClient('user', int(loader.api_id), loader.api_hash)
    await client.connect()
    print("--- telethon client connected ---")
    await client.start(phone=loader.phone_number)
    print("--- telethon client started ---")

    @client.on(events.NewMessage(chats=int(loader.chat_id)))
    async def new_message_listener(event):
        currency, amount = extract_amount_and_currency(event.message.text)
        if currency and amount:
            service = IncomeService()
            await service.insert_income(event.chat_id, amount, currency)

    try:
        print("--- telethon client running until disconnected ---")
        await client.run_until_disconnected()
    finally:
        print("--- start_telethon_client() finished ---")
        await client.disconnect()


async def main():
    print("--- main() starting ---")
    try:
        # Initialize database
        init_db()
        
        # Load credentials
        loader = CredentialLoader()
        await loader.load_credentials()
        
        # Start both clients
        print("--- before asyncio.gather() ---")
        await asyncio.gather(
            start_telegram_bot(loader.bot_token),
            start_telethon_client(loader)
        )
        print("--- after asyncio.gather() ---")
    except Exception as e:
        print(f"Error in main: {e}")
        raise
    finally:
        print("--- main() finished ---")

if __name__ == "__main__":
    print("--- if __name__ == '__main__' ---")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user")