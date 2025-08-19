from typing import Optional

from helper.logger_utils import force_log
from services.chat_service import ChatService
from services.shift_service import ShiftService


class ThresholdWarningService:
    """
    Service to handle threshold checking and warning messages.
    This service runs within telethon client to send warnings directly.
    """
    
    def __init__(self, telethon_client=None):
        self.telethon_client = telethon_client
        self.shift_service = ShiftService()
    
    async def check_and_send_warnings(
        self, 
        chat_id: int, 
        shift_id: Optional[int],
        new_income_amount: float,
        new_income_currency: str
    ):
        """
        Check if shift totals are below thresholds and send warning messages.
        Called after income is saved to database.
        """
        try:
            # Only check if we have a shift_id and telethon_client
            if not shift_id or not self.telethon_client:
                return
            
            force_log(f"ThresholdWarningService: Checking thresholds for chat {chat_id}, shift {shift_id}")
            
            # Get thresholds for this chat
            thresholds = await ChatService.get_chat_thresholds(chat_id)
            if not thresholds:
                force_log(f"ThresholdWarningService: No thresholds set for chat {chat_id}")
                return
            
            # Get current shift summary
            shift_summary = await self.shift_service.get_shift_income_summary(shift_id, chat_id)
            currencies = shift_summary.get("currencies", {})
            
            warnings_to_send = []
            
            # Check KHR threshold
            if (thresholds.get("khr_threshold") is not None and "KHR" in currencies):
                khr_amount = currencies["KHR"]["amount"]
                khr_threshold = thresholds["khr_threshold"]
                
                if khr_amount < khr_threshold:
                    warning_msg = (
                        f"⚠️ **ការព្រមាន**: ចំនួនប្រាក់ KHR ប្រចាំវេន "
                        f"({khr_amount:,.0f}) ទាបជាងកម្រិតកំណត់ ({khr_threshold:,.0f})"
                    )
                    warnings_to_send.append(warning_msg)
            
            # Check USD threshold  
            if (thresholds.get("usd_threshold") is not None and "USD" in currencies):
                usd_amount = currencies["USD"]["amount"]
                usd_threshold = thresholds["usd_threshold"]
                
                if usd_amount < usd_threshold:
                    warning_msg = (
                        f"⚠️ **ការព្រមាន**: ចំនួនប្រាក់ USD ប្រចាំវេន "
                        f"({usd_amount:.2f}) ទាបជាងកម្រិតកំណត់ ({usd_threshold:.2f})"
                    )
                    warnings_to_send.append(warning_msg)
            
            # Send warnings if any
            for warning_msg in warnings_to_send:
                await self._send_warning_message(chat_id, warning_msg)
                    
        except Exception as e:
            force_log(f"ThresholdWarningService: Error in check_and_send_warnings: {e}", "ERROR")
    
    async def _send_warning_message(self, chat_id: int, warning_msg: str):
        """Send threshold warning message to the chat"""
        try:
            await self.telethon_client.send_message(
                entity=chat_id,
                message=warning_msg,
                parse_mode='md'
            )
            force_log(f"ThresholdWarningService: Sent warning to chat {chat_id}: {warning_msg}")
        except Exception as send_error:
            force_log(f"ThresholdWarningService: Error sending warning: {send_error}", "ERROR")