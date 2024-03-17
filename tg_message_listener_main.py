from telethon import TelegramClient, events
import asyncio
import json
# Import your handler functions
from dexscreener_tg_message_listener import handle_dexscreener_message
from dextools_tg_message_listener import handle_dextools_message
from direct_address_tg_listener import handle_direct_address_message

async def load_credentials():
    with open('credentials_telegram.json', 'r') as f:
        credentials = json.load(f)
    return credentials

async def main():
    credentials = await load_credentials()

    client = TelegramClient('anon', credentials['api_id'], credentials['api_hash'])
    await client.start(bot_token=credentials['bot_token_1'])

    @client.on(events.NewMessage(chats=int(credentials['chat_id_1'])))
    async def new_message_listener(event):
        loop = asyncio.get_event_loop()
        if "dexscreener.com/ethereum/" in event.message.text:
            await loop.run_in_executor(None, handle_dexscreener_message, event.message.text)
        elif "dextools.io/app/en/ether/pair-explorer/" in event.message.text:
            await loop.run_in_executor(None, handle_dextools_message, event.message.text)
        else:
            await loop.run_in_executor(None, handle_direct_address_message, event.message.text)

    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
