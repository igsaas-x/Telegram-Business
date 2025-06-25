import asyncio

from alembic import command
from alembic.config import Config

from config import load_environment
from config.database_config import create_db_tables
from helper.credential_loader import CredentialLoader
from services import TelegramBotService, TelethonClientService

load_environment()


async def main():
    try:
        loader = CredentialLoader()
        telegramBotService = TelegramBotService()
        telethonClientService = TelethonClientService()

        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")

        create_db_tables()
        await loader.load_credentials()
        await asyncio.gather(
            telegramBotService.start(loader.bot_token),
            telethonClientService.start(loader.phone_number, loader),
            telethonClientService.start(loader.phone_number1, loader)
        )

    except Exception as e:
        print(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user")
