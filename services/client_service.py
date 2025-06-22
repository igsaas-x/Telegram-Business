import os
from telethon import TelegramClient, events
from database import get_all_chat_ids
from helper.message_parser import extract_amount_and_currency
from models.income_balance import IncomeService

async def start_telethon_client(loader):
    client = TelegramClient('user', int(os.getenv('API_ID')), os.getenv('API_HASH'))
    await client.connect()
    await client.start(phone=loader.phone_number)

    @client.on(events.NewMessage(chats=get_all_chat_ids()))
    async def new_message_listener(event):
        currency, amount = extract_amount_and_currency(event.message.text)
        if currency and amount:
            income_service = IncomeService()
            await income_service.add_income(
                chat_id=event.chat_id,
                currency=currency,
                amount=amount
            )

    print("Telethon client is running...")
    await client.run_until_disconnected()