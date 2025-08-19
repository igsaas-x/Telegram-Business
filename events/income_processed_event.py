from typing import Optional

from .base_event import BaseEvent


class IncomeProcessedEvent(BaseEvent):
    """Event fired when income has been processed and saved to database"""
    
    def __init__(
        self,
        chat_id: int,
        shift_id: Optional[int],
        amount: float,
        currency: str,
        income_balance_id: int,
        message_id: int,
        **kwargs
    ):
        data = {
            "chat_id": chat_id,
            "shift_id": shift_id,
            "amount": amount,
            "currency": currency,
            "income_balance_id": income_balance_id,
            "message_id": message_id,
            **kwargs
        }
        super().__init__(event_type="income.processed", data=data)
    
    @property
    def chat_id(self) -> int:
        return self.data["chat_id"]
    
    @property
    def shift_id(self) -> Optional[int]:
        return self.data["shift_id"]
    
    @property
    def amount(self) -> float:
        return self.data["amount"]
    
    @property
    def currency(self) -> str:
        return self.data["currency"]
    
    @property
    def income_balance_id(self) -> int:
        return self.data["income_balance_id"]
    
    @property
    def message_id(self) -> int:
        return self.data["message_id"]