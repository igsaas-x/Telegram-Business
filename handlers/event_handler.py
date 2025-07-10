from telethon import Button

from helper import DateUtils
from models import ChatService, ConversationService, IncomeService, UserService
from models.user_model import User
from .client_command_handler import CommandHandler


class EventHandler:
    def __init__(self):
        self.command_handler = CommandHandler()
        self.chat_service = ChatService()
        self.income_service = IncomeService()

    async def menu(self, event):
        # Check if chat is activated and trial status
        chat = await self.chat_service.get_chat_by_chat_id(str(event.chat_id))
        if not chat:
            # Chat doesn't exist - automatically register using our own register method
            try:
                # Get sender information
                sender = await event.get_sender()
                
                # Check if sender is anonymous
                if not sender or not hasattr(sender, 'id') or sender.id is None:
                    message = "⚠️ Registration failed: You must be a non-anonymous user to register this chat. Please disable anonymous mode and try again."
                    await event.respond(message)
                    return
                
                # Create user if not exists
                user_service = UserService()
                user = await user_service.create_user(sender)
                
                # Use our own register method to register the chat
                await self.register(event, user)
                
                # Refresh chat information after registration
                chat = await self.chat_service.get_chat_by_chat_id(str(event.chat_id))
                
                # If still not available, registration failed
                if not chat:
                    return  # Register method would have shown appropriate message
                
                # No need to show success message here since register method already does that
                
            except Exception as e:
                import logging
                logging.error(f"Error during auto-registration: {e}")
                message = "⚠️ Auto-registration failed. Please use /register command manually."
                await event.respond(message)
                return
        
        # Check if chat is not active (needs trial period check)
        if not chat.is_active:
            # Check if it's still within 7-day trial period
            from datetime import timedelta
            trial_end = chat.created_at + timedelta(days=7)
            
            # Make trial_end timezone-aware for comparison
            trial_end = DateUtils.localize_datetime(trial_end)
            
            if DateUtils.now() > trial_end:
                # Trial expired - ask user to contact admin
                message = "សូមទាក់ទងទៅអ្នកគ្រប់គ្រង: https://t.me/HK_688"
                
                # Check if this is a callback (return button) or new command
                if hasattr(event, 'callback_query') and event.callback_query:
                    await event.edit(message)
                else:
                    await event.respond(message)
                return
            # If within trial period, continue to show menu (don't update is_active)
        
        # Chat is either active (is_active=True) or within trial period - show menu
        buttons = [
            [
                Button.inline(
                    "ប្រចាំថ្ងៃ",
                    "daily_summary",
                )
            ],
            [Button.inline("ប្រចាំសប្តាហ៍", "weekly_summary")],
            [Button.inline("ប្រចាំខែ", "monthly_summary")],
            [Button.inline("បិទ", "close_menu")],
        ]
        
        # Check if this is a callback (return button) or new command
        if hasattr(event, 'callback_query') and event.callback_query:
            # This is from a return button - edit existing message
            await event.edit("ជ្រើសរើសរបាយការណ៍ប្រចាំ:", buttons=buttons)
        else:
            # This is from a new command - send new message
            await event.respond("ជ្រើសរើសរបាយការណ៍ប្រចាំ:", buttons=buttons)

    async def close_menu(self, event):
        await event.delete()

    async def register(self, event, user: User | None):
        chat_id = event.chat_id
        # Handle both group chats (with title) and private chats (without title)
        group_name = getattr(event.chat, 'title', f"Private Chat {chat_id}")
        chat_service = ChatService()
        success, message = await chat_service.register_chat_id(chat_id, group_name, user)
        
        # Add a menu button to the response message for successful registration
        if success:
            # Create menu button
            buttons = [
                [Button.inline("របាយការណ៍", "menu")]
            ]
            await event.respond(message, buttons=buttons)
        else:
            # For failures, just show the message without buttons
            await event.respond(message)

    async def message(self, event):
        if event.message.text.startswith("/"):
            return

        replied_message = await event.message.get_reply_message()
        if not replied_message:
            return

        chat_id = event.chat_id
        conversation_service = ConversationService()
        question = await conversation_service.get_question_by_message_id(
            chat_id=chat_id, message_id=replied_message.id
        )

        if question and question.question_type == "date_input":  # type: ignore
            await self.command_handler.handle_date_input_response(event, question)
            return

    async def callback(self, event):
        data = event.data.decode()
        if any(
            data.startswith(prefix) for prefix in ["summary_week_", "summary_month_"]
        ):
            await self.command_handler.handle_period_summary(event, data)
            return

        command_handlers = {
            "menu": self.menu,
            "daily_summary": self.command_handler.handle_daily_summary,
            "weekly_summary": self.command_handler.handle_weekly_summary,
            "monthly_summary": self.command_handler.handle_monthly_summary,
            "report_per_shift": self.command_handler.handle_report_per_shift,
            "close_shift": self.command_handler.close_shift,
            "close": self.command_handler.close,
            "close_menu": self.close_menu,
            "other_dates": self.command_handler.handle_other_dates,
        }

        handler = command_handlers.get(data)
        if handler:
            await handler(event)
            return

        if data.startswith("summary_of_"):
            await self.command_handler.handle_date_summary(event, data)
            return

        await self.command_handler.handle_daily_summary(event)
