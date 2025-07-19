import json
from datetime import datetime, timedelta

from telethon import Button

from common.enums import ServicePackage
from helper import total_summary_report, daily_transaction_report, DateUtils
from helper.logger_utils import force_log
from services import (
    ConversationService,
    IncomeService,
    ChatService,
    GroupPackageService,
)


class CommandHandler:
    def __init__(self):
        self.chat_service = ChatService()
        self.group_package_service = GroupPackageService()

    async def format_totals_message(self, period_text: str, incomes, chat_id: int = None, report_date: datetime = None, requesting_user=None):
        # Check if this is a daily report (contains "ថ្ងៃទី")
        if "ថ្ងៃទី" in period_text:
            # This is a daily report, use the new format
            if not report_date:
                # Try to extract date from period_text or use today
                report_date = DateUtils.now()
            
            # Get username from the requesting user (who triggered the request)
            telegram_username = "Admin"
            if requesting_user:
                if hasattr(requesting_user, 'username') and requesting_user.username:
                    telegram_username = requesting_user.username
                elif hasattr(requesting_user, 'first_name') and requesting_user.first_name:
                    telegram_username = requesting_user.first_name
                # If user is anonymous, username will remain "Admin"
            
            return daily_transaction_report(incomes, report_date, telegram_username)
        else:
            # This is a period report (weekly/monthly), use the old format
            title = f"សរុបប្រតិបត្តិការ {period_text}"
            return total_summary_report(incomes, title)

    async def handle_date_input_response(self, event, question):
        try:
            day_str = event.message.text.strip()
            day = int(day_str)

            if day < 1 or day > 31:
                await event.respond("ថ្ងៃមិនត្រឹមត្រូវ។ សូមជ្រើសរើសថ្ងៃពី 1 ដល់ 31។")
                return

            conversation_service = ConversationService()
            context_data = {}
            if question.context_data:
                context_data = json.loads(question.context_data)

            current_month = context_data.get(
                "current_month", DateUtils.now().strftime("%Y-%m")
            )
            date_str = f"{current_month}-{day:02d}"

            try:
                selected_date = datetime.strptime(date_str, "%Y-%m-%d")
                await conversation_service.mark_as_replied(
                    chat_id=event.chat_id, message_id=question.message_id
                )

                income_service = IncomeService()
                incomes = await income_service.get_income_by_date_and_chat_id(
                    chat_id=event.chat_id,
                    start_date=selected_date,
                    end_date=selected_date + timedelta(days=1),
                )

                # Don't delete user's reply message
                if not incomes:
                    await event.respond(
                        f"គ្មានប្រតិបត្តិការសម្រាប់ថ្ងៃទី {selected_date.strftime('%d %b %Y')} ទេ។"
                    )
                    return

                message = await self.format_totals_message(
                    f"ថ្ងៃទី {selected_date.strftime('%d %b %Y')}", incomes, event.chat_id, selected_date, event.sender
                )
                await event.client.send_message(event.chat_id, message)

            except ValueError:
                await event.respond("ទម្រង់កាលបរិច្ឆេទមិនត្រឹមត្រូវ")

        except ValueError:
            await event.respond("សូមវាយថ្ងៃជាលេខពី 1 ដល់ 31")
        except Exception as e:
            force_log(f"Error in handle_date_input_response: {e}")
            await event.respond("មានបញ្ហាក្នុងការដំណើរការសំណើរបស់អ្នក។ សូមព្យាយាមម្តងទៀត។")

    async def close(self, event):
        await self.handle_daily_summary(event)

    async def handle_current_date_summary(self, event):
        """Handle current date summary for basic package users with record limit"""
        chat_id = event.chat_id
        today = DateUtils.now()

        # Check package type
        group_package = await self.group_package_service.get_package_by_chat_id(chat_id)

        try:
            income_service = IncomeService()
            incomes = await income_service.get_income_by_specific_date_and_chat_id(
                chat_id=chat_id,
                target_date=today,
            )

            await event.delete()

            if not incomes:
                await event.client.send_message(
                    chat_id,
                    f"គ្មានប្រតិបត្តិការសម្រាប់ថ្ងៃទី {today.strftime('%d %b %Y')} ទេ។",
                )
                return

            # Check package limits
            if group_package and group_package.package == ServicePackage.FREE and len(incomes) > 20:
                contact_message = "អ្នកមានទិន្នន័យច្រើនជាង 20 កំណត់ត្រា។ សម្រាប់មើលទិន្នន័យពេញលេញ សូមប្រើប្រាស់កញ្ចប់ BASIC ឬប្រើប្រាស់កញ្ចប់ឥតកំណត់។\n\nសូមទាក់ទងទៅអ្នកគ្រប់គ្រង: https://t.me/HK_688"
                await event.client.send_message(chat_id, contact_message)
                return

            message = await self.format_totals_message(
                f"ថ្ងៃទី {today.strftime('%d %b %Y')}", incomes, chat_id, today, event.sender
            )
            await event.client.send_message(chat_id, message)

        except ValueError:
            await event.client.send_message(chat_id, "ទម្រង់កាលបរិច្ឆេទមិនត្រឹមត្រូវ")

    async def handle_daily_summary(self, event):
        today = DateUtils.now()
        buttons = []

        # Show 3 days for all chats
        for i in range(2, -1, -1):
            day = today - timedelta(days=i)
            label = day.strftime("%b %d")
            callback_value = day.strftime("%Y-%m-%d")
            buttons.append([Button.inline(label, f"summary_of_{callback_value}")])

        buttons.append([Button.inline("ថ្ងៃផ្សេងទៀត", "other_dates")])
        buttons.append([Button.inline("ត្រឡប់ក្រោយ", "menu")])

        await event.edit("ឆែករបាយការណ៍ថ្ងៃ:", buttons=buttons)

    async def handle_weekly_summary(self, event):
        now = DateUtils.now()
        
        # Get this week's Monday (start of current week)
        this_week_monday = now - timedelta(days=now.weekday())
        
        # Get last week's Monday (start of previous week)
        last_week_monday = this_week_monday - timedelta(days=7)
        
        buttons = []
        
        # Add this week button
        this_week_sunday = this_week_monday + timedelta(days=6)
        if this_week_monday.month != this_week_sunday.month:
            this_week_label = f"សប្តាហ៍នេះ ({this_week_monday.strftime('%d %b')} - {this_week_sunday.strftime('%d %b %Y')})"
        else:
            this_week_label = f"សប្តាហ៍នេះ ({this_week_monday.strftime('%d')} - {this_week_sunday.strftime('%d %b %Y')})"
        
        this_week_callback = this_week_monday.strftime("%Y-%m-%d")
        buttons.append([Button.inline(this_week_label, f"summary_week_{this_week_callback}")])
        
        # Add last week button
        last_week_sunday = last_week_monday + timedelta(days=6)
        if last_week_monday.month != last_week_sunday.month:
            last_week_label = f"សប្តាហ៍មុន ({last_week_monday.strftime('%d %b')} - {last_week_sunday.strftime('%d %b %Y')})"
        else:
            last_week_label = f"សប្តាហ៍មុន ({last_week_monday.strftime('%d')} - {last_week_sunday.strftime('%d %b %Y')})"
        
        last_week_callback = last_week_monday.strftime("%Y-%m-%d")
        buttons.append([Button.inline(last_week_label, f"summary_week_{last_week_callback}")])

        buttons.append([Button.inline("ត្រឡប់ក្រោយ", "menu")])
        await event.edit("ជ្រើសរើសសប្តាហ៍:", buttons=buttons)

    async def handle_monthly_summary(self, event):
        now = DateUtils.now()
        year = now.year
        buttons = []

        for month in range(1, 13):
            month_date = datetime(year, month, 1)
            label = month_date.strftime("%B %Y")
            callback_value = month_date.strftime("%Y-%m")
            buttons.append([Button.inline(label, f"summary_month_{callback_value}")])

        buttons.append([Button.inline("ត្រឡប់ក្រោយ", "menu")])
        await event.edit("ជ្រើសរើសខែ:", buttons=buttons)

    async def handle_other_dates(self, event):
        chat_id = event.chat_id

        result = await event.client.send_message(
            chat_id,
            "ឆែករបាយការណ៍ថ្ងៃទី:\n\nសូមវាយថ្ងៃ (1-31) ជាការឆ្លើយតបសារនេះដោយប្រើប៊ូតុង 'Reply' ឬ 'ឆ្លើយតប'",
        )

        conversation_service = ConversationService()
        current_month = DateUtils.now().strftime("%Y-%m")
        context_data = json.dumps({"current_month": current_month})
        await conversation_service.save_question(
            chat_id=chat_id,
            message_id=result.id,
            question_type="date_input",
            context_data=context_data,
        )
        await event.delete()

    async def handle_date_summary(self, event, data):
        chat_id = event.chat_id
        date_str = data.replace("summary_of_", "")

        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d")
            income_service = IncomeService()
            incomes = await income_service.get_income_by_date_and_chat_id(
                chat_id=chat_id,
                start_date=selected_date,
                end_date=selected_date + timedelta(days=1),
            )

            await event.answer(
                f"Fetching data for {selected_date.strftime('%d %b %Y')}"
            )
            await event.delete()
            if not incomes:
                await event.client.send_message(
                    chat_id,
                    f"គ្មានប្រតិបត្តិការសម្រាប់ថ្ងៃទី {selected_date.strftime('%d %b %Y')} ទេ។",
                )
                return

            message = await self.format_totals_message(
                f"ថ្ងៃទី {selected_date.strftime('%d %b %Y')}", incomes, chat_id, selected_date, event.sender
            )
            await event.client.send_message(chat_id, message)

        except ValueError:
            await event.client.send_message(chat_id, "ទម្រង់កាលបរិច្ឆេទមិនត្រឹមត្រូវ")

    async def handle_period_summary(self, event, data):
        chat_id = event.chat_id

        try:
            if data.startswith("summary_week_"):
                start_date = datetime.strptime(
                    data.replace("summary_week_", ""), "%Y-%m-%d"
                )
                end_date = start_date + timedelta(days=7)
                period_text = f"{start_date.strftime('%d')} - {(end_date - timedelta(days=1)).strftime('%d %b %Y')}"
            elif data.startswith("summary_month_"):
                start_date = datetime.strptime(
                    data.replace("summary_month_", ""), "%Y-%m"
                )
                from calendar import monthrange

                _, last_day = monthrange(start_date.year, start_date.month)
                end_date = start_date.replace(day=last_day) + timedelta(days=1)
                period_text = start_date.strftime("%B %Y")
            else:
                raise ValueError("Invalid period format")

            await event.answer(f"Fetching data for {period_text}")

            await event.delete()
            income_service = IncomeService()
            incomes = await income_service.get_income_by_date_and_chat_id(
                chat_id=chat_id, start_date=start_date, end_date=end_date
            )

            if not incomes:
                await event.client.send_message(
                    chat_id, f"គ្មានប្រតិបត្តិការសម្រាប់ {period_text} ទេ។"
                )
                return

            message = await self.format_totals_message(period_text, incomes, chat_id, None, event.sender)
            await event.client.send_message(chat_id, message)

        except ValueError:
            await event.client.send_message(chat_id, "ទម្រង់កាលបរិច្ឆេទមិនត្រឹមត្រូវ")
