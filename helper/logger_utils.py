import datetime
from pathlib import Path


class RotatingLogger:
    """Centralized logging utility with hourly log rotation"""
    
    @staticmethod
    def log(message: str, component: str = "System"):
        """
        Write logs with hourly rotation
        
        Args:
            message: The log message to write
            component: The component name (e.g., "TelethonClient", "MessageScheduler")
        """
        try:
            # Create logs directory if it doesn't exist
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)
            
            # Generate filename with current hour
            now = datetime.datetime.now()
            filename = f"telegram_bot_{now.strftime('%Y%m%d_%H')}.log"
            log_path = logs_dir / filename
            
            # Format the log entry
            timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
            log_entry = f"{timestamp} - {component} - {message}\n"
            
            # Write to the hourly log file
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
                f.flush()
                
        except Exception as e:
            # Fallback to simple file logging if anything goes wrong
            try:
                with open("telegram_bot_fallback.log", "a", encoding="utf-8") as f:
                    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    f.write(f"{timestamp} - {component} - LOGGER_ERROR: {e}\n")
                    f.write(f"{timestamp} - {component} - {message}\n")
                    f.flush()
            except:
                # If even fallback fails, just pass silently
                pass