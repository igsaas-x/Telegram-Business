import asyncio
import logging
import signal
from typing import Set

from alembic import command
from alembic.config import Config

from config import load_environment
from helper.credential_loader import CredentialLoader
from services.telegram_bot_service import TelegramBotService
from services.telethon_client_service import TelethonClientService
from schedulers import AutoCloseScheduler
from services.autosum_business_bot_service import AutosumBusinessBot
from services.telegram_admin_bot_service import TelegramAdminBot

load_environment()


# Configure logging first, before any services are imported
# Custom handler that ensures logs are written to file immediately
class ForceFileHandler(logging.FileHandler):
    """Custom handler that ensures logs are written to file immediately"""

    def emit(self, record):
        super().emit(record)
        self.flush()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[ForceFileHandler("telegram_bot.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

tasks: Set[asyncio.Task] = set()


def handle_signals(loop: asyncio.AbstractEventLoop) -> None:
    """
    Handle signal of event loop
    """
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(loop)))


async def shutdown(loop: asyncio.AbstractEventLoop) -> None:
    """
    Handle shut down of event loop
    """
    tasks_to_cancel = [t for t in tasks if not t.done()]
    if tasks_to_cancel:
        for task in tasks_to_cancel:
            task.cancel()
        await asyncio.gather(*tasks_to_cancel, return_exceptions=True)

    loop.stop()


async def main(loader: CredentialLoader) -> None:
    """
    Main function
    """
    try:
        telegramBotService = TelegramBotService()
        telethonClientService1 = TelethonClientService()
        adminBot = TelegramAdminBot(loader.admin_bot_token)
        businessBot = AutosumBusinessBot(loader.autosum_business_bot_token)
        autoCloseScheduler = AutoCloseScheduler(bot_service=businessBot)

        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")

        loop = asyncio.get_running_loop()
        handle_signals(loop)

        # Start all services
        service_tasks = [
            asyncio.create_task(telegramBotService.start(loader.bot_token)),
            asyncio.create_task(
                telethonClientService1.start(
                    loader.phone_number1, loader.api_id1, loader.api_hash1
                )
            ),
            asyncio.create_task(adminBot.start_polling()),
            asyncio.create_task(autoCloseScheduler.start_scheduler()),
        ]

        # Add business bot only if token is provided
        if loader.autosum_business_bot_token:
            logger.info("Starting business bot...")
            service_tasks.append(asyncio.create_task(businessBot.start_polling()))
        else:
            logger.warning("Business bot token not provided, skipping business bot")

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
