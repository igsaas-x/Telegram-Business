import asyncio

from helper.logger_utils import force_log
from services import ShiftService
from services.chat_service import ChatService
from services.private_bot_group_binding_service import PrivateBotGroupBindingService
from services.telegram_business_bot_service import AutosumBusinessBot


class AutoCloseScheduler:
    """Dedicated scheduler for auto-closing shifts that runs every minute"""

    def __init__(self, bot_service: AutosumBusinessBot):
        self.shift_service = ShiftService()
        self.chat_service = ChatService()
        self.bot_service = bot_service
        self.is_running = False

    async def start_scheduler(self):
        """Start the auto-close scheduler to run every minute"""
        self.is_running = True
        force_log("Auto-close scheduler started - will run every minute", "AutoCloseScheduler")

        while self.is_running:
            try:
                await self.check_auto_close_shifts()
                # Wait 1 minute (60 seconds) before next run
                await asyncio.sleep(60)
            except Exception as e:
                force_log(f"Error in auto-close scheduler loop: {e}", "AutoCloseScheduler", "ERROR")
                # Wait 1 minute before retrying if there's an error
                await asyncio.sleep(60)

    async def stop_scheduler(self):
        """Stop the auto-close scheduler"""
        self.is_running = False
        force_log("Auto-close scheduler stopped", "AutoCloseScheduler")

    async def check_auto_close_shifts(self):
        """Check and auto-close shifts based on configuration"""
        force_log("Starting auto-close shift check...", "AutoCloseScheduler", "DEBUG")

        try:
            # Use the existing method from ShiftService to check and auto-close all shifts
            closed_shifts = await self.shift_service.check_and_auto_close_shifts()

            if closed_shifts:
                force_log(
                    f"Auto-closed {len(closed_shifts)} shifts: {[shift['id'] for shift in closed_shifts]}", "AutoCloseScheduler"
                )

                # Send shift summaries to chats
                for shift in closed_shifts:
                    force_log(
                        f"Auto-closed shift {shift['id']} for chat {shift['chat_id']}", "AutoCloseScheduler"
                    )

                    # Send shift summary to chat if bot service is available
                    if self.bot_service:
                        await self._send_shift_summary(shift)
            else:
                force_log("No shifts needed auto-closing", "AutoCloseScheduler", "DEBUG")

        except Exception as e:
            force_log(f"Error in auto-close shift check: {e}", "AutoCloseScheduler", "ERROR")
            import traceback

            force_log(f"Traceback: {traceback.format_exc()}", "AutoCloseScheduler", "ERROR")

    async def _send_shift_summary(self, shift_info: dict):
        """Send shift summary to the chat"""
        try:
            chat_id = shift_info["chat_id"]
            shift_id = shift_info["id"]
            shift_number = shift_info["number"]

            # Get shift details for timing information
            shift = await self.shift_service.get_shift_by_id(shift_id)
            
            # Get shift summary
            summary = await self.shift_service.get_shift_income_summary(
                shift_id, chat_id
            )

            # Check if this group uses private bot binding
            chat = await self.chat_service.get_chat_by_chat_id(chat_id)
            group_id = chat.id if chat else None
            private_chats = PrivateBotGroupBindingService.get_private_chats_for_group(group_id) if group_id else []
            uses_private_bot = len(private_chats) > 0
            
            # Ensure shift has end_time (should be closed by auto-close)
            if not shift.end_time:
                force_log(f"Shift {shift_id} has no end_time, cannot generate summary", "AutoCloseScheduler", "WARN")
                return

            # Calculate shift duration
            duration = shift.end_time - shift.start_time
            total_seconds = abs(duration.total_seconds())
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)

            # Format date for the report header
            report_date = shift.end_time.strftime('%Y-%m-%d')

            # Get group name
            group_name = chat.group_name if chat and chat.group_name else "ក្រុម"

            # Format currency data
            currencies = summary.get("currencies", {})
            khr_data = currencies.get("KHR", {"amount": 0, "count": 0})
            usd_data = currencies.get("USD", {"amount": 0, "count": 0})

            # Format KHR and USD amounts
            khr_amount = int(khr_data["amount"])
            khr_count = khr_data["count"]
            usd_amount = usd_data["amount"]
            usd_count = usd_data["count"]

            # Format currency data for alignment
            khr_formatted = f"{khr_amount:,}"
            usd_formatted = f"{usd_amount:.2f}"

            # Calculate spacing for alignment
            max_amount_length = max(len(khr_formatted), len(usd_formatted))
            khr_spaces_needed = max_amount_length - len(khr_formatted) + 4
            usd_spaces_needed = max_amount_length - len(usd_formatted) + 4

            # Format the summary message with HTML
            if uses_private_bot:
                # For private groups, don't include transaction summary
                message = f"""របាយការណ៍ថ្ងៃ៖{report_date}

🏪 <b>ក្រុម:</b> {group_name}
🔢 <b>វេនទី:</b> {shift_number} | ម៉ោង: {shift.start_time.strftime('%I:%M %p')} - {shift.end_time.strftime('%I:%M %p')}
✅ <b>ស្ថានភាព:</b> បានបិទ

⏱️ <b>រយ:ពេល:</b> {hours}ម៉ោង:{minutes}នាទី
⚡ បិទដោយ: ការកំណត់ពេលវេលាស្វ័យប្រវត្តិ"""
            else:
                # For regular groups, include transaction summary with HTML formatting
                tabular_data = f"KHR: {khr_formatted}{' ' * khr_spaces_needed}| ប្រតិបត្តិការ: {khr_count}\n"
                tabular_data += f"USD: {usd_formatted}{' ' * usd_spaces_needed}| ប្រតិបត្តិការ: {usd_count}"

                message = f"""របាយការណ៍ថ្ងៃ៖{report_date}

🏪 <b>ក្រុម:</b> {group_name}
🔢 <b>វេនទី:</b> {shift_number} | ម៉ោង: {shift.start_time.strftime('%I:%M %p')} - {shift.end_time.strftime('%I:%M %p')}
✅ <b>ស្ថានភាព:</b> បានបិទ
<b>សរុបប្រតិបត្តការណ៍:</b>
<pre>{tabular_data}</pre>
⏱️ <b>រយ:ពេល:</b> {hours}ម៉ោង:{minutes}នាទី
⚡ បិទដោយ: ការកំណត់ពេលវេលាស្វ័យប្រវត្តិ"""

            # Check if daily summary on shift close feature is enabled
            from services import GroupPackageService
            from common.enums import FeatureFlags

            group_package_service = GroupPackageService()
            daily_summary_enabled = await group_package_service.has_feature(
                chat_id, FeatureFlags.DAILY_SUMMARY_ON_SHIFT_CLOSE.value
            )

            if daily_summary_enabled:
                # Add daily summary to the message in the requested format
                from services import IncomeService
                from datetime import timedelta

                income_service = IncomeService()

                # Get all transactions from first shift start time to last shift end time for this date
                # Use the shift's start date to find all shifts for that date
                shift_date = shift.start_time.date()
                shifts_for_date = await self.shift_service.get_shifts_by_date(chat_id, shift_date)

                if shifts_for_date:
                    # Find the earliest shift start time and latest shift end time for this date
                    earliest_start = min(s.start_time for s in shifts_for_date)
                    # Only consider shifts that have end_time (completed shifts)
                    completed_shifts = [s for s in shifts_for_date if s.end_time]
                    if completed_shifts:
                        latest_end = max(s.end_time for s in completed_shifts)
                        start_of_day = earliest_start
                        end_of_day = latest_end
                    else:
                        # If no completed shifts, use current shift's end time
                        start_of_day = earliest_start
                        end_of_day = shift.end_time
                else:
                    # Fallback if no shifts found
                    start_of_day = shift.start_time
                    end_of_day = shift.end_time

                incomes = await income_service.get_income_by_date_and_chat_id(
                    chat_id=chat_id,
                    start_date=start_of_day,
                    end_date=end_of_day
                )

                if incomes:
                    # Calculate totals for the entire day
                    daily_totals = {"KHR": 0, "USD": 0}
                    daily_counts = {"KHR": 0, "USD": 0}

                    for income in incomes:
                        currency = income.currency
                        if currency in daily_totals:
                            daily_totals[currency] += income.amount
                            daily_counts[currency] += 1

                    # Format daily summary in requested format with HTML
                    daily_khr_amount = int(daily_totals['KHR'])
                    daily_usd_amount = daily_totals['USD']

                    # Format daily summary data for alignment
                    daily_khr_formatted = f"{daily_khr_amount:,}"
                    daily_usd_formatted = f"{daily_usd_amount:.2f}"

                    # Calculate spacing for daily summary alignment
                    daily_max_length = max(len(daily_khr_formatted), len(daily_usd_formatted))
                    daily_khr_spaces = daily_max_length - len(daily_khr_formatted) + 4
                    daily_usd_spaces = daily_max_length - len(daily_usd_formatted) + 4

                    daily_tabular_data = f"KHR: {daily_khr_formatted}{' ' * daily_khr_spaces}| ប្រតិបត្តិការ: {daily_counts['KHR']}\n"
                    daily_tabular_data += f"USD: {daily_usd_formatted}{' ' * daily_usd_spaces}| ប្រតិបត្តិការ: {daily_counts['USD']}"

                    message += f"""


——----- summary ———----
📊 <b>សរុបថ្ងៃ {report_date}:</b>
<pre>{daily_tabular_data}</pre>"""

            # Send message with HTML parse mode
            success = await self.bot_service.send_message(chat_id, message, parse_mode="HTML")
            if success:
                force_log(f"Sent shift summary for shift {shift_id} to chat {chat_id}", "AutoCloseScheduler")
            else:
                force_log(
                    f"Failed to send shift summary for shift {shift_id} to chat {chat_id}", "AutoCloseScheduler", "WARN"
                )

        except Exception as e:
            force_log(
                f"Error sending shift summary for shift {shift_info.get('id', 'unknown')}: {e}", "AutoCloseScheduler", "ERROR"
            )
            import traceback

            force_log(f"Shift summary error traceback: {traceback.format_exc()}", "AutoCloseScheduler", "ERROR")
