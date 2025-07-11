import os
from typing import Optional

from dotenv import load_dotenv


def load_environment(env: Optional[str] = None) -> None:
    current_env = (env or os.getenv('APP_ENV'))
    
    # Load .env.local first if it exists (highest priority)
    if os.path.exists('.env.local'):
        load_dotenv(dotenv_path='.env.local')
    
    # Then load .env as fallback
    if os.path.exists('.env'):
        load_dotenv(dotenv_path='.env')
    
    # Finally load environment-specific file
    env_file = f'.env.{current_env}'
    if os.path.exists(env_file):
        load_dotenv(dotenv_path=env_file, override=True)
    
load_environment()
CURRENT_ENV = os.getenv('APP_ENV', 'local') 


__all__ = [
    'CURRENT_ENV',
]   