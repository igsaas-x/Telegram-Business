import uuid
from abc import ABC
from datetime import datetime
from typing import Any, Dict


class BaseEvent(ABC):
    """Base class for all events in the system"""
    
    def __init__(self, event_type: str, data: Dict[str, Any] = None):
        self.event_id = str(uuid.uuid4())
        self.event_type = event_type
        self.timestamp = datetime.utcnow()
        self.data = data or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary representation"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(event_id={self.event_id}, event_type={self.event_type})"