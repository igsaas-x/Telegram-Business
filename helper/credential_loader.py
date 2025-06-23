import os

class CredentialLoader:
    REQUIRED_ENV_VARS = [
        'API_ID',
        'API_HASH',
        'PHONE_NUMBER',
        'BOT_TOKEN',
        'BOT_NAME',
        'DB_USER',
        'DB_HOST',
        'DB_NAME',
        'API_ID1',
        'API_HASH1',
        'PHONE_NUMBER1'
    ]

    def __init__(self):
        self.api_id: str = ""
        self.api_hash: str = ""
        self.phone_number: str = ""
        self.bot_token: str = ""
        self.bot_name: str = ""
        self.db_user: str = ""
        self.db_password: str = ""
        self.db_host: str = ""
        self.db_name: str = ""
        self.api_id1: str = ""
        self.api_hash1: str = ""
        self.phone_number1: str = ""

    async def load_credentials(self) -> dict:
        missing = []
        self.api_id = os.getenv('API_ID') or ""
        self.api_hash = os.getenv('API_HASH') or ""
        self.phone_number = os.getenv('PHONE_NUMBER') or ""
        self.bot_token = os.getenv('BOT_TOKEN') or ""
        self.bot_name = os.getenv('BOT_NAME') or ""
        self.db_user = os.getenv('DB_USER') or ""
        self.db_password = os.getenv('DB_PASSWORD') or ""
        self.db_host = os.getenv('DB_HOST') or ""
        self.db_name = os.getenv('DB_NAME') or ""
        self.api_id1 = os.getenv('API_ID1') or ""
        self.api_hash1 = os.getenv('API_HASH1') or ""
        self.phone_number1 = os.getenv('PHONE_NUMBER1') or ""

        for var in self.REQUIRED_ENV_VARS:
            if not getattr(self, var.lower()):
                missing.append(var)

        if missing:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

        return {
            "api_id": self.api_id,
            "api_hash": self.api_hash,
            "phone_number": self.phone_number,
            "bot_token": self.bot_token,
            "bot_name": self.bot_name,
            "api_id1": self.api_id,
            "api_hash1": self.api_hash,
            "phone_number1": self.phone_number
        }
