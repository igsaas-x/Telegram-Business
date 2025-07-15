import os
from typing import Optional

from dotenv import load_dotenv


def load_environment(env: Optional[str] = None) -> None:
    """
    Load the environment variables from the .env file.
    """
    current_env = env or os.getenv("APP_ENV")

    if os.path.exists(".env.local"):
        load_dotenv(dotenv_path=".env.local")

    if os.path.exists(".env"):
        load_dotenv(dotenv_path=".env")

    env_file = f".env.{current_env}"
    if os.path.exists(env_file):
        load_dotenv(dotenv_path=env_file, override=True)
