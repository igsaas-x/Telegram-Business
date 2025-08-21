#!/usr/bin/env python3
"""
Test script for Service Monitor
Tests the monitoring functionality without running the full monitor
"""
import asyncio
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from service_monitor import ServiceMonitor


async def test_service_monitor():
    """Test the service monitor functionality"""
    print("🧪 Testing Service Monitor...")
    print("=" * 50)
    
    try:
        # Initialize monitor
        monitor = ServiceMonitor()
        print("✅ Service monitor initialized successfully")
        
        # Test service checking
        print("\n📋 Testing service status checking...")
        is_running_process = monitor.check_service_running()
        is_running_systemd = monitor.check_systemd_service()
        
        print(f"  Process check result: {is_running_process}")
        print(f"  Systemd check result: {is_running_systemd}")
        
        overall_status = is_running_process or is_running_systemd
        print(f"  Overall service status: {'🟢 RUNNING' if overall_status else '🔴 STOPPED'}")
        
        # Test alert configuration
        print("\n🔔 Testing alert configuration...")
        if monitor.admin_bot:
            print("  ✅ Admin bot configured")
        else:
            print("  ⚠️  Admin bot not configured (ADMIN_BOT_TOKEN missing)")
            
        if monitor.admin_chat_id:
            print(f"  ✅ Admin chat ID configured: {monitor.admin_chat_id}")
        else:
            print("  ⚠️  Admin chat ID not configured (ADMIN_ALERT_CHAT_ID missing)")
            
        # Test alert sending (dry run)
        print("\n📤 Testing alert mechanism...")
        if monitor.admin_bot and monitor.admin_chat_id:
            try:
                test_message = "🧪 **Test Alert from Service Monitor**\n\nThis is a test message to verify the alerting system is working correctly."
                success = await monitor.send_alert(test_message)
                if success:
                    print("  ✅ Test alert sent successfully!")
                else:
                    print("  ❌ Failed to send test alert")
            except Exception as e:
                print(f"  ❌ Error sending test alert: {e}")
        else:
            print("  ⚠️  Cannot test alert sending - bot or chat ID not configured")
            
        print("\n📊 Configuration Summary:")
        print(f"  Service name: {monitor.service_name}")
        print(f"  Check interval: {monitor.check_interval} seconds")
        print(f"  Alert cooldown: {monitor.alert_cooldown}")
        print(f"  Service command pattern: {monitor.service_command_pattern}")
        
        print("\n✅ Service monitor test completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_service_monitor())