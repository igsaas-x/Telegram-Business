from telethon import TelegramClient, events
from helper.message_parser import extract_amount_and_currency
from models import ChatService, IncomeService


class TelethonClientService:
    def __init__(self):
        self.client = None
        
    async def start(self,username, loader):
        self.client = TelegramClient(username, int(loader.api_id), loader.api_hash)
        await self.client.connect()
        await self.client.start(phone=loader.phone_number) #type: ignore

        chat_service = ChatService()

        @self.client.on(events.NewMessage) #type: ignore
        async def new_message_listener(event):
            chat_ids = chat_service.get_all_chat_ids()
            if event.chat_id not in chat_ids:
                return
            currency, amount = extract_amount_and_currency(event.message.text)
            if currency and amount:
                service = IncomeService()
                await service.insert_income(event.chat_id, amount, currency, amount) #type: ignore

        await self.client.run_until_disconnected() #type: ignore