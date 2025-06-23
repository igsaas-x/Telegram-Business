from datetime import datetime, timedelta
from calendar import monthrange
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class DateRange:
    start_date: datetime
    end_date: datetime
    label: str
    callback_value: str

class DateHelper:
    @staticmethod
    def get_week_ranges(year: int, month: int) -> List[DateRange]:
        _, last_day = monthrange(year, month)
        ranges = [(1, 8), (8, 15), (15, 22), (22, last_day + 1)]
        
        return [
            DateHelper._create_week_range(year, month, start_day, end_day)
            for start_day, end_day in ranges
        ]
    
    @staticmethod
    def _create_week_range(year: int, month: int, start_day: int, end_day: int) -> DateRange:
        start_date = datetime(year, month, start_day)
        end_date = datetime(year, month, min(end_day, monthrange(year, month)[1]))
        label = f"{start_date.strftime('%d')} - {(end_date - timedelta(days=1)).strftime('%d %b %Y')}"
        callback_value = start_date.strftime("%Y-%m-%d")
        
        return DateRange(start_date, end_date, label, f"summary_week_{callback_value}") 