import asyncio
import signal
from typing import Set

from alembic import command
from alembic.config import Config

from config import load_environment
from config.database_config import create_db_tables
from helper.credential_loader import CredentialLoader
from services import TelegramBotService, TelethonClientService
from services.telegram_admin_bot_service import TelegramAdminBot

load_environment()
tasks: Set[asyncio.Task] = set()


def handle_signals(loop: asyncio.AbstractEventLoop) -> None:
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(loop)))


async def shutdown(loop: asyncio.AbstractEventLoop) -> None:
    tasks_to_cancel = [t for t in tasks if not t.done()]
    if tasks_to_cancel:
        for task in tasks_to_cancel:
            task.cancel()
        await asyncio.gather(*tasks_to_cancel, return_exceptions=True)

    loop.stop()


async def main(loader: CredentialLoader) -> None:
    try:
        telegramBotService = TelegramBotService()
        telethonClientService = TelethonClientService()
        telethonClientService1 = TelethonClientService()
        adminBot = TelegramAdminBot(loader.admin_bot_token)

        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        create_db_tables()

        loop = asyncio.get_running_loop()
        handle_signals(loop)

        # Start all services
        service_tasks = [
            asyncio.create_task(telegramBotService.start(loader.bot_token)),
            asyncio.create_task(
                telethonClientService.start(
                    loader.phone_number, loader.api_id, loader.api_hash
                )
            ),
            asyncio.create_task(
                telethonClientService1.start(
                    loader.phone_number1, loader.api_id1, loader.api_hash1
                )
            ),
            asyncio.create_task(adminBot.start_polling()),
        ]

        tasks.update(service_tasks)
        await asyncio.gather(*service_tasks)

    except Exception as e:
        print(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    try:
        loader = CredentialLoader()
        loader.load_credentials()
        asyncio.run(main(loader))

    except KeyboardInterrupt:
        print("\nBot stopped by user")
