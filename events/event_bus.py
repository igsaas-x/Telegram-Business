import asyncio
from typing import Dict, List, Callable

from helper.logger_utils import force_log
from .base_event import BaseEvent


class EventBus:
    """Simple event bus for publishing and subscribing to events"""
    
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
        self._global_listeners: List[Callable] = []
    
    def subscribe(self, event_type: str, listener: Callable[[BaseEvent], None]):
        """Subscribe to a specific event type"""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)
        force_log(f"EventBus: Subscribed to {event_type}")
    
    def subscribe_all(self, listener: Callable[[BaseEvent], None]):
        """Subscribe to all events"""
        self._global_listeners.append(listener)
        force_log("EventBus: Subscribed to all events")
    
    async def publish(self, event: BaseEvent):
        """Publish an event to all subscribers"""
        try:
            force_log(f"EventBus: Publishing event {event.event_type} (ID: {event.event_id})")
            
            # Get specific listeners for this event type
            specific_listeners = self._listeners.get(event.event_type, [])
            
            # Combine with global listeners
            all_listeners = specific_listeners + self._global_listeners
            
            if not all_listeners:
                force_log(f"EventBus: No listeners for event {event.event_type}")
                return
            
            # Run all listeners concurrently
            tasks = []
            for listener in all_listeners:
                if asyncio.iscoroutinefunction(listener):
                    tasks.append(listener(event))
                else:
                    # For non-async functions, run in executor
                    tasks.append(asyncio.get_event_loop().run_in_executor(None, listener, event))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                force_log(f"EventBus: Processed {len(tasks)} listeners for event {event.event_type}")
            
        except Exception as e:
            force_log(f"EventBus: Error publishing event {event.event_type}: {e}", "ERROR")
    
    def unsubscribe(self, event_type: str, listener: Callable):
        """Unsubscribe a listener from an event type"""
        if event_type in self._listeners and listener in self._listeners[event_type]:
            self._listeners[event_type].remove(listener)
            force_log(f"EventBus: Unsubscribed from {event_type}")
    
    def clear_listeners(self, event_type: str = None):
        """Clear listeners for a specific event type, or all if none specified"""
        if event_type:
            self._listeners[event_type] = []
        else:
            self._listeners.clear()
            self._global_listeners.clear()
        force_log(f"EventBus: Cleared listeners for {event_type or 'all events'}")


# Global event bus instance
event_bus = EventBus()