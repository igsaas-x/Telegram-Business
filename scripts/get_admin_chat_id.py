#!/usr/bin/env python3
"""
Helper script to get admin chat ID for service monitor alerts
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from telegram import Bot
from config import load_environment
from helper.credential_loader import CredentialLoader


async def get_chat_id():
    """Get recent chat updates to find admin group chat ID"""
    try:
        # Load environment and credentials
        load_environment()
        loader = CredentialLoader()
        loader.load_credentials(mode="bots_only")
        
        if not hasattr(loader, 'admin_bot_token') or not loader.admin_bot_token:
            print("❌ ADMIN_BOT_TOKEN not found in environment")
            print("Please set ADMIN_BOT_TOKEN in your .env file")
            return
            
        # Initialize bot
        bot = Bot(token=loader.admin_bot_token)
        
        print("🔍 Fetching recent updates from admin bot...")
        print("Note: The bot must have received messages recently to show in updates")
        print()
        
        # Get updates
        updates = await bot.get_updates()
        
        if not updates:
            print("📭 No recent updates found.")
            print()
            print("To find your admin group chat ID:")
            print("1. Add your admin bot to the admin group")
            print("2. Send a message in the group (mention the bot or send any message)")
            print("3. Run this script again")
            print()
            print("Alternatively, visit:")
            print(f"https://api.telegram.org/bot{loader.admin_bot_token}/getUpdates")
            print("And look for the 'chat':{'id': value")
            return
            
        print(f"📨 Found {len(updates)} recent update(s):")
        print()
        
        unique_chats = {}
        
        for update in updates:
            if update.message:
                chat = update.message.chat
                chat_id = chat.id
                chat_title = chat.title or chat.first_name or "Unknown"
                chat_type = chat.type
                
                if chat_id not in unique_chats:
                    unique_chats[chat_id] = {
                        'title': chat_title,
                        'type': chat_type,
                        'id': chat_id
                    }
        
        for chat_id, chat_info in unique_chats.items():
            chat_type_emoji = {
                'group': '👥',
                'supergroup': '👥', 
                'private': '👤',
                'channel': '📢'
            }.get(chat_info['type'], '❓')
            
            print(f"{chat_type_emoji} {chat_info['title']}")
            print(f"   Chat ID: {chat_info['id']}")
            print(f"   Type: {chat_info['type']}")
            
            if chat_info['type'] in ['group', 'supergroup']:
                print(f"   ✅ Use this for ADMIN_ALERT_CHAT_ID: {chat_info['id']}")
            
            print()
            
        print("💡 Tips:")
        print("- Group and supergroup IDs are negative numbers")
        print("- Choose the admin group where you want to receive service alerts")
        print("- Add this to your .env file:")
        print(f"  ADMIN_ALERT_CHAT_ID=<chat_id_from_above>")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(get_chat_id())