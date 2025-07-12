import asyncio

from helper.logger_utils import force_log
from models.shift_model import ShiftService


class AutoCloseScheduler:
    """Dedicated scheduler for auto-closing shifts that runs every minute"""
    
    def __init__(self):
        self.shift_service = ShiftService()
        self.is_running = False

    async def start_scheduler(self):
        """Start the auto-close scheduler to run every minute"""
        self.is_running = True
        force_log("Auto-close scheduler started - will run every minute")

        while self.is_running:
            try:
                await self.check_auto_close_shifts()
                # Wait 1 minute (60 seconds) before next run
                await asyncio.sleep(60)
            except Exception as e:
                force_log(f"Error in auto-close scheduler loop: {e}")
                # Wait 1 minute before retrying if there's an error
                await asyncio.sleep(60)

    async def stop_scheduler(self):
        """Stop the auto-close scheduler"""
        self.is_running = False
        force_log("Auto-close scheduler stopped")

    async def check_auto_close_shifts(self):
        """Check and auto-close shifts based on configuration"""
        force_log("Starting auto-close shift check...")
        
        try:
            # Use the existing method from ShiftService to check and auto-close all shifts
            closed_shifts = await self.shift_service.check_and_auto_close_shifts()
            
            if closed_shifts:
                force_log(f"Auto-closed {len(closed_shifts)} shifts: {[shift.id for shift in closed_shifts]}")
                for shift in closed_shifts:
                    force_log(f"Auto-closed shift {shift.id} for chat {shift.chat_id}")
            else:
                force_log("No shifts needed auto-closing")
                
        except Exception as e:
            force_log(f"Error in auto-close shift check: {e}")
            import traceback
            force_log(f"Traceback: {traceback.format_exc()}")