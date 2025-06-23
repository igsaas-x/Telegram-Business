import os
from dotenv import load_dotenv
from typing import Optional

def load_environment(env: Optional[str] = None) -> None:
    current_env = (env or os.getenv('APP_ENV'))
    if os.path.exists('.env'):
        load_dotenv(dotenv_path='.env')
    
    env_file = f'.env.{current_env}'
    if os.path.exists(env_file):
        load_dotenv(dotenv_path=env_file, override=True)
    
    if current_env == 'local' and os.path.exists('.env.local'):
        load_dotenv(dotenv_path='.env.local', override=True)
    
load_environment()
CURRENT_ENV = os.getenv('APP_ENV', 'local') 