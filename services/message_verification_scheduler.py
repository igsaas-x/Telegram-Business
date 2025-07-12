import asyncio
import datetime
import logging
from typing import List

import pytz
from telethon import TelegramClient
from telethon.tl.types import Message

from helper import extract_amount_and_currency, extract_trx_id
from models import ChatService, IncomeService


def force_log(message):
    """Write logs to telegram_bot.log since normal logging doesn't work"""
    with open("telegram_bot.log", "a") as f:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"{timestamp} - MessageVerificationScheduler - INFO - {message}\n")
        f.flush()


logger = logging.getLogger(__name__)


class MessageVerificationScheduler:
    def __init__(self, telethon_client: TelegramClient):
        self.client = telethon_client
        self.chat_service = ChatService()
        self.income_service = IncomeService()
        self.is_running = False

    async def start_scheduler(self):
        """Start the scheduler to run every 10 minutes"""
        self.is_running = True
        force_log("Message verification scheduler started - will run every 10 minutes")
        
        while self.is_running:
            try:
                await self.verify_messages()
                # Wait 10 minutes (600 seconds) before next run
                await asyncio.sleep(600)
            except Exception as e:
                force_log(f"Error in scheduler loop: {e}")
                # Wait 1 minute before retrying if there's an error
                await asyncio.sleep(60)

    async def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False
        force_log("Message verification scheduler stopped")

    async def verify_messages(self):
        """Main verification method that reads messages from last 20 minutes"""
        force_log("Starting message verification job...")
        
        try:
            # Get all chat IDs from database
            chat_ids = await self.chat_service.get_all_chat_ids()
            force_log(f"Found {len(chat_ids)} chats to verify")
            
            # Calculate time range (last 30 minutes)
            now = datetime.datetime.now(pytz.UTC)
            twenty_minutes_ago = now - datetime.timedelta(minutes=30)
            force_log(f"Checking messages from {twenty_minutes_ago} to {now}")
            
            verification_count = 0
            new_messages_found = 0
            
            for chat_id in chat_ids:
                try:
                    # Get chat info to check if it's active
                    chat = await self.chat_service.get_chat_by_chat_id(chat_id)
                    if not chat or not chat.is_active:
                        force_log(f"Skipping inactive chat {chat_id}")
                        continue
                    
                    force_log(f"Verifying messages for chat {chat_id} ({chat.group_name})")
                    
                    # Read messages from the chat within the time range
                    messages = await self._get_bot_messages_in_timeframe(
                        chat_id, twenty_minutes_ago, now
                    )
                    
                    verification_count += len(messages)
                    
                    for message in messages:
                        await self._verify_and_store_message(chat, message)
                        new_messages_found += 1
                        
                except Exception as chat_error:
                    force_log(f"Error processing chat {chat_id}: {chat_error}")
                    continue
            
            force_log(f"Verification job completed. Checked {verification_count} messages, processed {new_messages_found} new messages")
            
        except Exception as e:
            force_log(f"Error in verify_messages: {e}")
            import traceback
            force_log(f"Traceback: {traceback.format_exc()}")

    async def _get_bot_messages_in_timeframe(
        self, chat_id: int, start_time: datetime.datetime, end_time: datetime.datetime
    ) -> List[Message]:
        """Get bot messages from a specific chat within the given timeframe"""
        messages = []
        
        try:
            # Get messages from the chat
            async for message in self.client.iter_messages(
                chat_id, 
                offset_date=end_time,
                reverse=True,
                limit=None
            ):
                # Check if message is within our time range
                message_time = message.date
                if message_time.tzinfo is None:
                    message_time = pytz.UTC.localize(message_time)
                
                if message_time < start_time:
                    # We've gone too far back in time
                    break
                
                if start_time <= message_time <= end_time:
                    # Check if message is from a bot
                    sender = await message.get_sender()
                    is_bot = getattr(sender, 'bot', False)
                    
                    if is_bot and message.text:
                        # Skip AutosumBusinessBot messages
                        if getattr(sender, 'username', '') != 'AutosumBusinessBot':
                            messages.append(message)
                            force_log(f"Found bot message in timeframe: {message.id} from {message_time}")
        
        except Exception as e:
            force_log(f"Error getting messages for chat {chat_id}: {e}")
        
        return messages

    async def _verify_and_store_message(self, chat, message: Message):
        """Verify if message exists in database, if not then store it"""
        try:
            chat_id = message.chat_id or chat.chat_id
            message_id = message.id
            message_text = message.text
            
            force_log(f"Verifying message {message_id} from chat {chat_id}")

            # Check message timestamp vs chat registration
            message_time = message.date
            if message_time.tzinfo is None:
                message_time = pytz.UTC.localize(message_time)

            # Convert chat created_at to UTC for comparison
            from helper import DateUtils
            chat_created = chat.created_at
            if chat_created.tzinfo is None:
                chat_created = DateUtils.localize_datetime(chat_created)
            chat_created_utc = chat_created.astimezone(pytz.UTC)

            if message_time < chat_created_utc:
                force_log(
                    f"Message {message_id} timestamp {message_time} is before chat registration {chat_created_utc}, skipping")
                return
            
            # Check if this message already exists in database (using both chat_id and message_id)
            exists = await self.income_service.get_income_by_chat_and_message_id(chat_id, message_id)
            if exists:
                force_log(f"Message {message_id} from chat {chat_id} already exists in database, skipping")
                return
            
            # Extract currency and amount from message
            currency, amount = extract_amount_and_currency(message_text)
            if not (currency and amount):
                force_log(f"No valid currency/amount found in message {message_id}, skipping")
                return
            
            # Extract transaction ID
            trx_id = extract_trx_id(message_text)
            
            force_log(f"Processing new message {message_id}: currency={currency}, amount={amount}, trx_id={trx_id}")
            
            # Check for duplicates using comprehensive check
            # Not check for now, suppose chat_id + message_id is unique
            # is_duplicate = await self.income_service.check_duplicate_transaction(
            #     chat_id, trx_id, message_id
            # )
            # if is_duplicate:
            #     force_log(f"Duplicate transaction found for message {message_id}, skipping")
            #     return
            
            # Store the message as income
            force_log(f"Storing income for message {message_id}")
            result = await self.income_service.insert_income(
                chat_id,
                amount,
                currency,
                amount,  # original_amount
                message_id,
                message_text,
                trx_id,
                None,  # shift_id
                chat.enable_shift  # enable_shift
            )
            
            force_log(f"Successfully stored income record with id={result.id} for message {message_id}")
            
        except Exception as e:
            force_log(f"Error verifying/storing message {message.id}: {e}")
            import traceback
            force_log(f"Traceback: {traceback.format_exc()}")