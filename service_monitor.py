#!/usr/bin/env python3
"""
Service Monitor for Telegram Telethon Client
Monitors the main_telethon_only.py service and sends alerts via admin bot
"""
import asyncio
import logging
import signal
import subprocess
from datetime import datetime, timedelta

from telegram import Bot
from telegram.error import TelegramError

from config import load_environment
from helper.credential_loader import CredentialLoader


class ServiceMonitor:
    def __init__(self):
        self.is_running = False
        self.last_alert_time = None
        self.alert_cooldown = timedelta(minutes=30)  # Don't spam alerts
        self.check_interval = 60  # Check every 60 seconds
        self.service_name = "main_telethon_only.py"
        self.service_command_pattern = "python3 main_telethon_only.py"
        
        # Load environment and credentials
        load_environment()
        self.loader = CredentialLoader()
        self.loader.load_credentials(mode="bots_only")
        
        # Initialize bot for alerts
        self.admin_bot = None
        if hasattr(self.loader, 'admin_bot_token') and self.loader.admin_bot_token:
            self.admin_bot = Bot(token=self.loader.admin_bot_token)
        
        # Admin group chat ID for alerts (you'll need to set this)
        self.admin_chat_id = getattr(self.loader, 'admin_alert_chat_id', None)
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for the service monitor"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("service_monitor.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def check_service_running(self) -> bool:
        """
        Check if the Telethon service is running
        
        Returns:
            bool: True if service is running, False otherwise
        """
        try:
            # Check for running processes
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Look for the main telethon process
                for line in result.stdout.split('\n'):
                    if self.service_command_pattern in line and "grep" not in line:
                        self.logger.debug(f"Found running service: {line.strip()}")
                        return True
                        
            return False
            
        except subprocess.TimeoutExpired:
            self.logger.error("Timeout occurred while checking service status")
            return False
        except Exception as e:
            self.logger.error(f"Error checking service status: {e}")
            return False
            
    def check_systemd_service(self, service_name: str = "mytelethon") -> bool:
        """
        Check if systemd service is running (for production deployment)
        
        Args:
            service_name: Name of the systemd service
            
        Returns:
            bool: True if service is active, False otherwise
        """
        try:
            result = subprocess.run(
                ["systemctl", "is-active", service_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            is_active = result.stdout.strip() == "active"
            self.logger.debug(f"Systemd service {service_name} status: {'active' if is_active else 'inactive'}")
            return is_active
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout occurred while checking systemd service {service_name}")
            return False
        except FileNotFoundError:
            self.logger.warning("systemctl not found, falling back to process check")
            return False
        except Exception as e:
            self.logger.error(f"Error checking systemd service {service_name}: {e}")
            return False
            
    async def send_alert(self, message: str, is_recovery: bool = False) -> bool:
        """
        Send alert message to admin group
        
        Args:
            message: Alert message to send
            is_recovery: Whether this is a recovery notification
            
        Returns:
            bool: True if message was sent successfully
        """
        if not self.admin_bot or not self.admin_chat_id:
            self.logger.warning("Admin bot or admin chat ID not configured, cannot send alert")
            return False
            
        try:
            # Add emoji and formatting
            alert_emoji = "✅" if is_recovery else "🚨"
            formatted_message = f"{alert_emoji} **Service Monitor Alert**\n\n{message}\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            await self.admin_bot.send_message(
                chat_id=self.admin_chat_id,
                text=formatted_message,
                parse_mode='Markdown'
            )
            
            self.logger.info(f"Alert sent to admin chat {self.admin_chat_id}")
            return True
            
        except TelegramError as e:
            self.logger.error(f"Failed to send Telegram alert: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending alert: {e}")
            return False
            
    def should_send_alert(self) -> bool:
        """
        Check if enough time has passed since last alert (rate limiting)
        
        Returns:
            bool: True if alert should be sent
        """
        if self.last_alert_time is None:
            return True
            
        return datetime.now() - self.last_alert_time >= self.alert_cooldown
        
    async def monitor_service(self):
        """
        Main monitoring loop
        """
        self.logger.info("Starting service monitoring...")
        service_was_running = None
        consecutive_failures = 0
        max_consecutive_failures = 3  # Alert after 3 consecutive failures
        
        while self.is_running:
            try:
                # Check both process-based and systemd-based monitoring
                is_running_process = self.check_service_running()
                is_running_systemd = self.check_systemd_service()
                
                # Service is considered running if either check passes
                is_running = is_running_process or is_running_systemd
                
                self.logger.debug(f"Service status - Process: {is_running_process}, Systemd: {is_running_systemd}")
                
                if is_running:
                    consecutive_failures = 0
                    
                    # Send recovery notification if service was down
                    if service_was_running is False:
                        recovery_message = "🎉 **Telethon Service Recovered**\n\nThe main Telethon client service is now running normally."
                        await self.send_alert(recovery_message, is_recovery=True)
                        self.last_alert_time = datetime.now()
                        
                    service_was_running = True
                    self.logger.debug("Telethon service is running normally")
                    
                else:
                    consecutive_failures += 1
                    
                    # Send alert if service is down and we should alert
                    if service_was_running is not False and consecutive_failures >= max_consecutive_failures:
                        if self.should_send_alert():
                            alert_message = f"""🚨 **Telethon Service Down**

The main Telethon client service appears to be stopped or crashed.

**Details:**
- Service: {self.service_name}
- Check method: Process monitoring + Systemd
- Consecutive failures: {consecutive_failures}
- Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Action Required:**
Please check the server and restart the service if necessary.

**Commands to check:**
```
sudo systemctl status mytelethon
sudo systemctl restart mytelethon
ps aux | grep main_telethon_only.py
```"""

                            await self.send_alert(alert_message)
                            self.last_alert_time = datetime.now()
                            
                        service_was_running = False
                        self.logger.error(f"Telethon service is down (consecutive failures: {consecutive_failures})")
                    
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)
                
    async def start_monitoring(self):
        """Start the monitoring service"""
        self.is_running = True
        
        # Validate configuration
        if not self.admin_chat_id:
            self.logger.warning("Admin chat ID not configured. Set ADMIN_ALERT_CHAT_ID in environment.")
            
        if not self.admin_bot:
            self.logger.warning("Admin bot not configured. Set ADMIN_BOT_TOKEN in environment.")
            
        self.logger.info(f"Service monitor started. Checking every {self.check_interval} seconds.")
        self.logger.info(f"Monitoring service: {self.service_name}")
        self.logger.info(f"Alert cooldown: {self.alert_cooldown}")
        
        await self.monitor_service()
        
    def stop_monitoring(self):
        """Stop the monitoring service"""
        self.is_running = False
        self.logger.info("Service monitoring stopped")


def handle_signals(monitor: ServiceMonitor):
    """Handle shutdown signals"""
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}, shutting down...")
        monitor.stop_monitoring()
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main function"""
    monitor = ServiceMonitor()
    handle_signals(monitor)
    
    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\nService monitor stopped by user")
    except Exception as e:
        monitor.logger.error(f"Fatal error in service monitor: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())