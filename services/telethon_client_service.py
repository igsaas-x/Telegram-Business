from telethon import TelegramClient, events
from helper import extract_amount_and_currency, extract_trx_id
from models import ChatService, IncomeService


class TelethonClientService:
    def __init__(self):
        self.client = None
        self.service = IncomeService()
        
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
            message_id:int = event.message.id
            trx_id = extract_trx_id(event.message.text)

            if await self.service.get_income_by_message_id(message_id) and self.service.get_income_by_trx_id(trx_id):
                return
            
            if currency and amount and trx_id:
                await self.service.insert_income(event.chat_id, amount, currency, amount, message_id, event.message.text, trx_id)

        await self.client.run_until_disconnected() #type: ignore