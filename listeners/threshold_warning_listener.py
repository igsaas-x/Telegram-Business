from events import IncomeProcessedEvent, ThresholdWarningEvent, event_bus
from helper.logger_utils import force_log
from services.chat_service import ChatService
from services.shift_service import ShiftService


class ThresholdWarningListener:
    """
    Event listener that checks income thresholds and sends warnings.
    This listener runs with the bots and listens to events published from telethon.
    """
    
    def __init__(self, telegram_service=None):
        self.chat_service = ChatService()
        self.shift_service = ShiftService()
        self.telegram_service = telegram_service  # Bot service to send warnings
        self._is_listening = False
    
    async def start_listening(self):
        """Start listening to income processed events"""
        if self._is_listening:
            force_log("ThresholdWarningListener: Already listening")
            return
            
        force_log("ThresholdWarningListener: Starting to listen for income processed events")
        event_bus.subscribe("income.processed", self._on_income_processed)
        self._is_listening = True
    
    async def stop_listening(self):
        """Stop listening to events"""
        if not self._is_listening:
            return
            
        force_log("ThresholdWarningListener: Stopping event listener")
        event_bus.unsubscribe("income.processed", self._on_income_processed)
        self._is_listening = False
    
    async def _on_income_processed(self, event: IncomeProcessedEvent):
        """
        Handle income processed event by checking thresholds
        """
        try:
            force_log(f"ThresholdWarningListener: Processing income event for chat {event.chat_id}, amount: {event.amount} {event.currency}")
            
            # Get chat thresholds
            thresholds = await ChatService.get_chat_thresholds(event.chat_id)
            if not thresholds:
                force_log(f"ThresholdWarningListener: No thresholds set for chat {event.chat_id}")
                return
            
            # Only check if we have a shift_id (income is associated with a shift)
            if not event.shift_id:
                force_log(f"ThresholdWarningListener: No shift_id for income, skipping threshold check")
                return
            
            # Get current shift summary
            shift_summary = await self.shift_service.get_shift_income_summary(
                event.shift_id, event.chat_id
            )
            
            currencies = shift_summary.get("currencies", {})
            warnings_to_send = []
            
            # Check KHR threshold
            if (thresholds.get("khr_threshold") is not None and 
                "KHR" in currencies):
                
                khr_amount = currencies["KHR"]["amount"]
                khr_threshold = thresholds["khr_threshold"]
                
                if khr_amount < khr_threshold:
                    warning_msg = (
                        f"⚠️ **ការព្រមាន**: ចំនួនប្រាក់ KHR ប្រចាំវេន "
                        f"({khr_amount:,.0f}) ទាបជាងកម្រិតកំណត់ ({khr_threshold:,.0f})"
                    )
                    warnings_to_send.append(
                        ThresholdWarningEvent(
                            chat_id=event.chat_id,
                            shift_id=event.shift_id,
                            currency="KHR",
                            current_amount=khr_amount,
                            threshold_amount=khr_threshold,
                            warning_message=warning_msg
                        )
                    )
            
            # Check USD threshold  
            if (thresholds.get("usd_threshold") is not None and 
                "USD" in currencies):
                
                usd_amount = currencies["USD"]["amount"]
                usd_threshold = thresholds["usd_threshold"]
                
                if usd_amount < usd_threshold:
                    warning_msg = (
                        f"⚠️ **ការព្រមាន**: ចំនួនប្រាក់ USD ប្រចាំវេន "
                        f"({usd_amount:.2f}) ទាបជាងកម្រិតកំណត់ ({usd_threshold:.2f})"
                    )
                    warnings_to_send.append(
                        ThresholdWarningEvent(
                            chat_id=event.chat_id,
                            shift_id=event.shift_id,
                            currency="USD", 
                            current_amount=usd_amount,
                            threshold_amount=usd_threshold,
                            warning_message=warning_msg
                        )
                    )
            
            # Send warnings if any
            for warning_event in warnings_to_send:
                await self._send_threshold_warning(warning_event)
                # Also publish the warning event for other listeners
                await event_bus.publish(warning_event)
                
        except Exception as e:
            force_log(f"ThresholdWarningListener: Error processing income event: {e}", "ERROR")
    
    async def _send_threshold_warning(self, warning_event: ThresholdWarningEvent):
        """Send threshold warning message to the chat"""
        try:
            if not self.telegram_service:
                force_log("ThresholdWarningListener: No telegram service provided, cannot send warning")
                return
            
            force_log(f"ThresholdWarningListener: Sending threshold warning to chat {warning_event.chat_id}")
            
            # Send the warning message to the chat
            await self.telegram_service.send_message(
                chat_id=warning_event.chat_id,
                message=warning_event.warning_message,
                parse_mode="Markdown"
            )
            
            force_log(f"ThresholdWarningListener: Successfully sent warning for {warning_event.currency} threshold")
            
        except Exception as e:
            force_log(f"ThresholdWarningListener: Error sending threshold warning: {e}", "ERROR")