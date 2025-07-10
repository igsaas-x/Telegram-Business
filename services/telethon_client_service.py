import os

from telethon import TelegramClient, events
from telethon.errors import PersistentTimestampInvalidError

from helper import extract_amount_and_currency, extract_trx_id
from models import ChatService, IncomeService


class TelethonClientService:
    def __init__(self):
        self.client = None
        self.service = IncomeService()

    async def start(self, username, api_id, api_hash):
        session_file = f"{username}.session"
        
        # Handle persistent timestamp errors by removing corrupted session
        try:
            self.client = TelegramClient(username, int(api_id), api_hash)
            await self.client.connect()
            await self.client.start(phone=username)  # type: ignore
            print("Account " + username + " started...")
        except PersistentTimestampInvalidError:
            print(f"Session corrupted for {username}, removing session file...")
            if os.path.exists(session_file):
                os.remove(session_file)
            
            # Recreate client with clean session
            self.client = TelegramClient(username, int(api_id), api_hash)
            await self.client.connect()
            await self.client.start(phone=username)  # type: ignore
            print("Account " + username + " restarted with clean session...")

        chat_service = ChatService()

        # @self.client.on(events.NewMessage(pattern="/verify"))
        # async def _verify_current_date_report(event):
        #     chat = event.chat_id
        #     today = DateUtils.today()
        #     yesterday = today - timedelta(days=1)
        #     start_of_yesterday = DateUtils.start_of_day(yesterday)

        #     last_msg = await self.service.get_last_yesterday_message(start_of_yesterday)
        #     min_id = int(getattr(last_msg, "message_id", 0)) if last_msg else 0

        #     # Get when this client was added to the group
        #     try:
        #         me = await self.client.get_me()
        #         participants = await self.client.get_participants(chat)
        #         my_participant = next((p for p in participants if p.id == me.id), None)
                
        #         # If we can't find when we were added, use current time to avoid historical messages
        #         join_time = getattr(my_participant, 'date', DateUtils.now()) if my_participant else DateUtils.now()
        #     except Exception:
        #         # If we can't get join time, use current time as fallback
        #         join_time = DateUtils.now()

        #     incomes = []
        #     processed_ids = set()

        #     async for msg in self.client.iter_messages(  # type: ignore
        #         chat, search="paid by", min_id=min_id
        #     ):
        #         # Skip messages sent before we joined the group
        #         if msg.date < join_time:
        #             continue
        #         if not (msg.text and msg.date) or msg.id in processed_ids:
        #             continue

        #         currency, amount = extract_amount_and_currency(msg.text)
        #         trx_id = extract_trx_id(msg.text)
        #         processed_ids.add(msg.id)

        #         if not (currency and amount):
        #             continue

        #         currency_code = next(
        #             (c.name for c in CurrencyEnum if c.value == currency), None
        #         )
        #         if not currency_code:
        #             continue

        #         try:
        #             amount_value = float(str(amount).replace(",", "").replace(" ", ""))
        #         except Exception:
        #             continue

        #         incomes.append(
        #             IncomeBalance(
        #                 amount=amount_value,
        #                 chat_id=chat,
        #                 currency=currency_code,
        #                 original_amount=amount_value,
        #                 income_date=msg.date,
        #                 message_id=msg.id,
        #                 message=msg.text,
        #                 trx_id=trx_id,
        #             )
        #         )

        #     summary = total_summary_report(incomes, "របាយការណ៍សរុបប្រចាំថ្ងៃនេះ")
        #     await event.client.send_message(chat, summary)

        @self.client.on(events.NewMessage)  # type: ignore
        async def _new_message_listener(event):
            # Check if this is a private chat (not a group)
            if event.is_private:
                await event.respond("សូមទាក់ទងទៅអ្នកគ្រប់គ្រង: https://t.me/HK_688")
                return

            currency, amount = extract_amount_and_currency(event.message.text)
            message_id: int = event.message.id
            trx_id: str = extract_trx_id(event.message.text) or ""

            # Check for duplicate based on message_id first
            if await self.service.get_income_by_message_id(message_id):
                return

            # Check for duplicate based on trx_id only if trx_id exists
            if trx_id and await self.service.get_income_by_trx_id(trx_id):
                return

            # Only require currency and amount, trx_id is optional
            if currency and amount:
                
                # Check if chat exists, auto-register if not
                if not await chat_service.chat_exists(event.chat_id):
                    try:
                        # Get chat title for registration
                        chat_entity = await self.client.get_entity(event.chat_id)
                        chat_title = getattr(chat_entity, 'title', f"Chat {event.chat_id}")
                        
                        # Register the chat without a specific user (user=None)
                        success, _ = await chat_service.register_chat_id(event.chat_id, chat_title, None)
                        
                        if not success:
                            # If registration failed, skip this message
                            print(f"Failed to auto-register chat {event.chat_id}")
                            return
                            
                        print(f"Auto-registered chat: {event.chat_id} ({chat_title})")
                    except Exception as e:
                        print(f"Error during chat auto-registration: {e}")
                        return
                
                last_income = await self.service.get_last_shift_id(event.chat_id)
                shift_number: int = last_income.shift if last_income else 1  # type: ignore
                await self.service.insert_income(
                    event.chat_id,
                    amount,
                    currency,
                    amount,
                    message_id,
                    event.message.text,
                    trx_id,
                    shift_number,
                )

        await self.client.run_until_disconnected()  # type: ignore
