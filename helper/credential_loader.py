import os

class CredentialLoader:
    REQUIRED_ENV_VARS = [
        'API_ID',
        'API_HASH',
        'CHAT_ID',
        'PHONE_NUMBER',
        'BOT_TOKEN',
        'BOT_NAME',
        'DB_USER',
        'DB_HOST',
        'DB_NAME'
    ]

    def __init__(self):
        self.api_id: str = ""
        self.api_hash: str = ""
        self.chat_id: str = ""
        self.phone_number: str = ""
        self.bot_token: str = ""
        self.bot_name: str = ""
        self.db_user: str = ""
        self.db_password: str = ""
        self.db_host: str = ""
        self.db_name: str = ""

    async def load_credentials(self) -> dict:
        missing = []
        self.api_id = os.getenv('API_ID') or ""
        self.api_hash = os.getenv('API_HASH') or ""
        self.chat_id = os.getenv('CHAT_ID') or ""
        self.phone_number = os.getenv('PHONE_NUMBER') or ""
        self.bot_token = os.getenv('BOT_TOKEN') or ""
        self.bot_name = os.getenv('BOT_NAME') or ""
        self.db_user = os.getenv('DB_USER') or ""
        self.db_password = os.getenv('DB_PASSWORD') or ""
        self.db_host = os.getenv('DB_HOST') or ""
        self.db_name = os.getenv('DB_NAME') or ""

        for var in self.REQUIRED_ENV_VARS:
            if not getattr(self, var.lower()):
                missing.append(var)

        if missing:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

        return {
            "api_id": self.api_id,
            "api_hash": self.api_hash,
            "chat_id": self.chat_id,
            "phone_number": self.phone_number,
            "bot_token": self.bot_token,
            "bot_name": self.bot_name
        }
