import datetime
import os

def force_log(message, component="System"):
    """Write logs with hourly rotation"""
    try:
        # Ensure logs directory exists
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        # Generate filename with current hour for rotation
        now = datetime.datetime.now()
        filename = f"logs/telegram_bot_{now.strftime('%Y%m%d_%H')}.log"
        
        # Write to the hourly log file
        with open(filename, "a", encoding="utf-8") as f:
            timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{timestamp} - {component} - {message}\n")
            f.flush()
    except Exception as e:
        # Fallback to simple file if anything goes wrong
        try:
            with open("telegram_bot_fallback.log", "a") as f:
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"{timestamp} - {component} - LOGGER_ERROR: {e}\n")
                f.write(f"{timestamp} - {component} - {message}\n")
                f.flush()
        except:
            pass