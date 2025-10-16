from enum import Enum


class FeatureFlags(Enum):
    """
    Feature flags for group packages to enable/disable additional features
    """
    
    # Report features
    WEEKLY_MONTHLY_REPORTS = "weekly_monthly_reports"
    DAILY_BUSINESS_REPORTS = "daily_business_reports"
    ADVANCED_ANALYTICS = "advanced_analytics"
    
    # Transaction features
    TRANSACTION_ANNOTATION = "transaction_annotation"
    CUSTOM_REPORT = "custom_report"
    
    # Business features
    SHIFT_MANAGEMENT = "shift_management"
    SHIFT_PERMISSIONS = "shift_permissions"
    HIDE_LAST_SHIFT_OF_DAY = "hide_last_shift_of_day"
    DAILY_SUMMARY_ON_SHIFT_CLOSE = "daily_summary_on_shift_close"
    CUSTOM_WEEKLY_REPORT = "custom_weekly_report"
    CUSTOM_MONTHLY_REPORT = "custom_monthly_report"
