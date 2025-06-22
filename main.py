import asyncio
from dotenv import load_dotenv
from helper.credential_loader import CredentialLoader
from config.database_config import init_db
from services.bot_service import start_telegram_bot
from services.client_service import start_telethon_client

load_dotenv()

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