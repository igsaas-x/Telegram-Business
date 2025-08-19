from typing import Optional

from .base_event import BaseEvent


class ThresholdWarningEvent(BaseEvent):
    """Event fired when income balance is below threshold"""
    
    def __init__(
        self,
        chat_id: int,
        shift_id: Optional[int],
        currency: str,
        current_amount: float,
        threshold_amount: float,
        warning_message: str,
        **kwargs
    ):
        data = {
            "chat_id": chat_id,
            "shift_id": shift_id,
            "currency": currency,
            "current_amount": current_amount,
            "threshold_amount": threshold_amount,
            "warning_message": warning_message,
            **kwargs
        }
        super().__init__(event_type="threshold.warning", data=data)
    
    @property
    def chat_id(self) -> int:
        return self.data["chat_id"]
    
    @property
    def shift_id(self) -> Optional[int]:
        return self.data["shift_id"]
    
    @property
    def currency(self) -> str:
        return self.data["currency"]
    
    @property
    def current_amount(self) -> float:
        return self.data["current_amount"]
    
    @property
    def threshold_amount(self) -> float:
        return self.data["threshold_amount"]
    
    @property
    def warning_message(self) -> str:
        return self.data["warning_message"]