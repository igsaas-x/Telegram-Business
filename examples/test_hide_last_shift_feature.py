"""
Test Hide Last Shift Feature Flag

This file demonstrates how to use the HIDE_LAST_SHIFT_OF_DAY feature flag
to prevent showing the last (empty) shift of the day when there are no transactions.

Usage:
1. Enable the feature flag for a chat
2. When generating daily reports, the last shift will be filtered out if there are multiple shifts
"""

from common.enums import FeatureFlags
from services.group_package_service import GroupPackageService


async def test_hide_last_shift_feature():
    """Test the hide last shift feature flag"""
    
    service = GroupPackageService()
    chat_id = 123456789  # Example chat ID
    
    print("Testing HIDE_LAST_SHIFT_OF_DAY feature flag...")
    
    # 1. Enable the feature flag
    print("1. Enabling hide last shift feature...")
    await service.set_feature_flag(chat_id, FeatureFlags.HIDE_LAST_SHIFT_OF_DAY.value, True)
    
    # 2. Check if feature is enabled
    hide_last_shift = await service.has_feature(chat_id, FeatureFlags.HIDE_LAST_SHIFT_OF_DAY.value)
    print(f"Feature enabled: {hide_last_shift}")
    
    # 3. Simulate shift filtering logic
    print("\n3. Simulating shift filtering logic...")
    
    # Mock shifts data (normally retrieved from database)
    mock_shifts = [
        {"id": 1, "number": 1, "has_transactions": True},
        {"id": 2, "number": 2, "has_transactions": True},  
        {"id": 3, "number": 3, "has_transactions": False},  # Last shift with no transactions
    ]
    
    print(f"Original shifts count: {len(mock_shifts)}")
    
    # Apply the feature flag logic
    if hide_last_shift and len(mock_shifts) > 1:
        # Remove the last shift (highest number/latest created)
        filtered_shifts = mock_shifts[:-1]
        print(f"Filtered shifts count: {len(filtered_shifts)}")
        print("Last shift hidden successfully!")
    else:
        filtered_shifts = mock_shifts
        print(f"No filtering applied. Shifts count: {len(filtered_shifts)}")
    
    # 4. Test with feature disabled
    print("\n4. Testing with feature disabled...")
    await service.set_feature_flag(chat_id, FeatureFlags.HIDE_LAST_SHIFT_OF_DAY.value, False)
    
    hide_last_shift_disabled = await service.has_feature(chat_id, FeatureFlags.HIDE_LAST_SHIFT_OF_DAY.value)
    print(f"Feature enabled: {hide_last_shift_disabled}")
    
    if hide_last_shift_disabled and len(mock_shifts) > 1:
        filtered_shifts = mock_shifts[:-1]
        print(f"Filtered shifts count: {len(filtered_shifts)}")
    else:
        filtered_shifts = mock_shifts
        print(f"No filtering applied. Shifts count: {len(filtered_shifts)}")
    
    print("\nTest completed!")


async def setup_business_with_hide_last_shift(chat_id: int):
    """Setup a business package with hide last shift feature enabled"""
    
    service = GroupPackageService()
    
    # Business package features including the new hide last shift feature
    features = {
        FeatureFlags.TRANSACTION_ANNOTATION.value: True,
        FeatureFlags.DAILY_BUSINESS_REPORTS.value: True,
        FeatureFlags.ADVANCED_ANALYTICS.value: True,
        FeatureFlags.CUSTOM_EXPORT.value: True,
        FeatureFlags.SHIFT_MANAGEMENT.value: True,
        FeatureFlags.SHIFT_PERMISSIONS.value: True,
        FeatureFlags.API_ACCESS.value: True,
        FeatureFlags.HIDE_LAST_SHIFT_OF_DAY.value: True,  # New feature flag
    }
    
    await service.update_feature_flags(chat_id, features)
    print(f"Setup BUSINESS package with hide last shift feature for chat {chat_id}")
    print(f"Features: {features}")


if __name__ == "__main__":
    import asyncio
    
    # Run test
    asyncio.run(test_hide_last_shift_feature())
    asyncio.run(setup_business_with_hide_last_shift(123456789))