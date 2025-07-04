import os
from datetime import datetime, timedelta, time

import pytz


class DateUtils:
    """
    Utility class for handling dates and times with consistent timezone support
    """
    
    @staticmethod
    def get_timezone():
        """Get the configured timezone, defaults to Asia/Phnom_Penh"""
        timezone_name = os.getenv('TIMEZONE', 'Asia/Phnom_Penh')
        return pytz.timezone(timezone_name)
    
    @staticmethod
    def now():
        """Get current datetime in the configured timezone"""
        return datetime.now(DateUtils.get_timezone())
    
    @staticmethod
    def today():
        """Get current date in the configured timezone"""
        return DateUtils.now().date()
    
    @staticmethod
    def yesterday():
        """Get yesterday's date in the configured timezone"""
        return DateUtils.today() - timedelta(days=1)
    
    @staticmethod
    def start_of_day(date):
        """Get the start of the given date in the configured timezone"""
        tz = DateUtils.get_timezone()
        return datetime.combine(date, time.min, tzinfo=tz)
    
    @staticmethod
    def end_of_day(date):
        """Get the end of the given date in the configured timezone"""
        tz = DateUtils.get_timezone()
        return datetime.combine(date, time.max, tzinfo=tz)
    
    @staticmethod
    def start_of_yesterday():
        """Get the start of yesterday in the configured timezone"""
        return DateUtils.start_of_day(DateUtils.yesterday())
    
    @staticmethod
    def format_date(date, format_string='%d %b %Y'):
        """Format a date with the given format string"""
        if isinstance(date, datetime):
            return date.strftime(format_string)
        return date.strftime(format_string)
    
    @staticmethod
    def parse_date(date_string, format_string='%Y-%m-%d'):
        """Parse a date string with the given format"""
        return datetime.strptime(date_string, format_string)
    
    @staticmethod
    def localize_datetime(dt):
        """Localize a naive datetime to the configured timezone"""
        if dt.tzinfo is None:
            tz = DateUtils.get_timezone()
            return tz.localize(dt)
        return dt
    
    @staticmethod
    def days_ago(days):
        """Get a date that is N days ago from today"""
        return DateUtils.today() - timedelta(days=days)
    
    @staticmethod
    def add_days(date, days):
        """Add N days to the given date"""
        return date + timedelta(days=days)