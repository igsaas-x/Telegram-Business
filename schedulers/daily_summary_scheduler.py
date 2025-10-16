import asyncio
from datetime import datetime

import schedule

from helper.dateutils import DateUtils
from helper.logger_utils import force_log
from services.chat_service import ChatService
from services.income_balance_service import IncomeService
from services.private_bot_group_binding_service import PrivateBotGroupBindingService
from services.shift_service import ShiftService


class DailySummaryScheduler:
    """Scheduler that sends daily shift summaries to private groups using schedule library"""

    def __init__(self):
        self.shift_service = ShiftService()
        self.income_service = IncomeService()
        self.chat_service = ChatService()
        self.is_running = False
        self.scheduled_jobs = {}  # Track scheduled jobs by private_chat_id
        self.refresh_job = None  # Track the refresh job separately
        # Use a separate scheduler instance instead of global schedule
        self.scheduler = schedule.Scheduler()

    @staticmethod
    def _async_wrapper(coro):
        """Wrapper to schedule async coroutines from synchronous schedule library"""
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(coro)
        except Exception as e:
            force_log(f"Error in _async_wrapper: {e}", "DailySummaryScheduler", "ERROR")

    async def start_scheduler(self):
        """Start the daily summary scheduler using schedule library"""
        self.is_running = True
        force_log("Daily summary scheduler started", "DailySummaryScheduler")

        # Initial setup of scheduled jobs
        await self._setup_schedules()

        # Periodically refresh schedules (every 10 minutes) to pick up new/changed times
        # Store the refresh job reference so we don't cancel it later
        self.refresh_job = self.scheduler.every(10).minutes.do(
            lambda: self._async_wrapper(self._setup_schedules())
        )

        # Log once that the loop is starting
        force_log(f"Scheduler loop starting with {len(self.scheduler.jobs)} jobs", "DailySummaryScheduler", "DEBUG")

        loop_count = 0
        while self.is_running:
            try:
                # Run pending scheduled jobs
                self.scheduler.run_pending()

                # Every 60 seconds, log that we're still alive
                loop_count += 1
                if loop_count % 60 == 0:
                    force_log(
                        f"Scheduler loop alive, checking jobs (jobs: {len(self.scheduler.jobs)})",
                        "DailySummaryScheduler",
                        "DEBUG"
                    )

                # Sleep for 1 second to avoid busy waiting
                await asyncio.sleep(1)

            except Exception as e:
                force_log(f"Error in daily summary scheduler loop: {e}", "DailySummaryScheduler", "ERROR")
                import traceback
                force_log(f"Traceback: {traceback.format_exc()}", "DailySummaryScheduler", "ERROR")
                await asyncio.sleep(60)

    async def stop_scheduler(self):
        """Stop the daily summary scheduler"""
        self.is_running = False
        self.scheduler.clear()
        force_log("Daily summary scheduler stopped", "DailySummaryScheduler")

    async def _setup_schedules(self):
        """Setup scheduled jobs for all private chats with configured times"""
        force_log("Daily summary scheduler setup schedule", "DailySummaryScheduler")

        try:
            # Get all unique private chat configurations from service
            results = PrivateBotGroupBindingService.get_all_with_daily_summary_time()

            # Clear existing jobs (except the refresh job)
            for job in list(self.scheduler.jobs):
                # Don't cancel the refresh job
                if job == self.refresh_job:
                    continue
                self.scheduler.cancel_job(job)

            self.scheduled_jobs = {}

            for private_chat_id, time_str in results:
                if not time_str:
                    continue

                try:
                    # Validate time format
                    datetime.strptime(time_str, "%H:%M")

                    # Convert ICT time to server's local time for scheduling
                    local_time_str = DateUtils.convert_ict_time_to_local(time_str)

                    # Create a job for this private chat at the specified time
                    # Use _async_wrapper to properly schedule the async coroutine
                    job = self.scheduler.every().day.at(local_time_str).do(
                        lambda pc_id=private_chat_id: self._async_wrapper(
                            self._send_summary_to_private_chat(pc_id)
                        )
                    )

                    self.scheduled_jobs[private_chat_id] = job
                    force_log(
                        f"Scheduled daily summary for private chat {private_chat_id} at {time_str} ICT ({local_time_str} local)",
                        "DailySummaryScheduler"
                    )

                except ValueError:
                    force_log(
                        f"Invalid time format '{time_str}' for private chat {private_chat_id}",
                        "DailySummaryScheduler",
                        "WARN"
                    )

            force_log(f"Setup {len(self.scheduled_jobs)} scheduled summaries", "DailySummaryScheduler")

            # Debug: Show all schedule jobs
            force_log(f"Total jobs in this scheduler: {len(self.scheduler.jobs)}", "DailySummaryScheduler", "DEBUG")
            for job in self.scheduler.jobs:
                force_log(f"  Job: {job}, next_run: {job.next_run}", "DailySummaryScheduler", "DEBUG")

        except Exception as e:
            force_log(f"Error in _setup_schedules: {e}", "DailySummaryScheduler", "ERROR")
            import traceback
            force_log(f"Traceback: {traceback.format_exc()}", "DailySummaryScheduler", "ERROR")

    async def _send_summary_to_private_chat(self, private_chat_id: int):
        """Generate and send consolidated summary for a private chat"""
        force_log(
            f"🔔 SCHEDULED JOB TRIGGERED! Generating summary for private chat {private_chat_id}",
            "DailySummaryScheduler"
        )

        # Get all groups bound to this private chat
        groups = PrivateBotGroupBindingService.get_bound_groups(private_chat_id)

        if not groups:
            force_log(f"No groups bound to private chat {private_chat_id}", "DailySummaryScheduler")
            return

        force_log(f"Found {len(groups)} groups for private chat {private_chat_id}", "DailySummaryScheduler")

        # Consolidated totals across all groups
        total_khr_amount = 0
        total_usd_amount = 0.0
        total_khr_count = 0
        total_usd_count = 0
        summary_date = None

        # Process each group
        for group in groups:
            try:
                # Get the most recent closed shift
                recent_shifts = await self.shift_service.get_recent_closed_shifts(
                    group.chat_id, limit=1
                )

                if not recent_shifts:
                    force_log(
                        f"No closed shifts found for group {group.chat_id} ({group.group_name})",
                        "DailySummaryScheduler",
                        "DEBUG"
                    )
                    continue

                last_shift = recent_shifts[0]
                shift_start_date = last_shift.start_time.date()

                # Store the date for the report (use the first group's date)
                if summary_date is None:
                    summary_date = shift_start_date

                force_log(
                    f"Last closed shift for group {group.chat_id}: shift_date={shift_start_date}",
                    "DailySummaryScheduler",
                    "DEBUG"
                )

                # Get all shifts that started on this date
                shifts_on_date = await self.shift_service.get_shifts_by_start_date(
                    group.chat_id, shift_start_date
                )

                force_log(
                    f"Found {len(shifts_on_date)} shifts for {group.group_name} on {shift_start_date}",
                    "DailySummaryScheduler"
                )

                # Calculate totals for all shifts on this date
                for shift in shifts_on_date:
                    summary = await self.shift_service.get_shift_income_summary(
                        shift.id, group.chat_id
                    )

                    currencies = summary.get("currencies", {})
                    khr_data = currencies.get("KHR", {"amount": 0, "count": 0})
                    usd_data = currencies.get("USD", {"amount": 0, "count": 0})

                    total_khr_amount += int(khr_data["amount"])
                    total_usd_amount += usd_data["amount"]
                    total_khr_count += khr_data["count"]
                    total_usd_count += usd_data["count"]

            except Exception as e:
                force_log(
                    f"Error processing group {group.chat_id} ({group.group_name}): {e}",
                    "DailySummaryScheduler",
                    "ERROR"
                )
                import traceback
                force_log(f"Traceback: {traceback.format_exc()}", "DailySummaryScheduler", "ERROR")

        # If no data was collected, skip sending
        if summary_date is None:
            force_log(
                f"No shift data found for any group in private chat {private_chat_id}",
                "DailySummaryScheduler"
            )
            return

        # Format and send the consolidated message
        message = self._format_summary_message(
            summary_date,
            total_khr_amount,
            total_usd_amount,
            total_khr_count,
            total_usd_count
        )

        # Send to private chat using private bot
        from services.bot_registry import BotRegistry
        bot_registry = BotRegistry()
        private_bot = bot_registry.get_private_bot()

        if private_bot:
            success = await private_bot.send_message(private_chat_id, message)
            if success:
                force_log(
                    f"Sent daily summary to private chat {private_chat_id}",
                    "DailySummaryScheduler"
                )
            else:
                force_log(
                    f"Failed to send daily summary to private chat {private_chat_id}",
                    "DailySummaryScheduler",
                    "WARN"
                )
        else:
            force_log("Private bot not available", "DailySummaryScheduler", "WARN")

    @staticmethod
    def _format_summary_message(
        shift_date,
        total_khr_amount: int,
        total_usd_amount: float,
        total_khr_count: int,
        total_usd_count: int
    ) -> str:
        """Format the summary message following the reference format"""
        # Format currency amounts
        khr_formatted = f"{total_khr_amount:,.0f}"
        usd_formatted = f"{total_usd_amount:.2f}"

        # Calculate spacing for alignment
        max_amount_length = max(len(khr_formatted), len(usd_formatted))
        khr_spaces_needed = max_amount_length - len(khr_formatted) + 4
        usd_spaces_needed = max_amount_length - len(usd_formatted) + 4

        # Format date as DD-MM-YYYY
        date_str = shift_date.strftime('%d-%m-%Y')

        # Build message following reference format from menu_handler.py:425-427
        message = "\n\n" + "——----- summary ———----" + "\n"
        message += f"📊 <b>សរុបវេនទាំងអស់ថ្ងៃ {date_str}:</b>\n"

        # Wrap totals in pre tags for proper alignment
        total_data = f"KHR: {khr_formatted}{' ' * khr_spaces_needed}| ប្រតិបត្តិការ: {total_khr_count}\n"
        total_data += f"USD: {usd_formatted}{' ' * usd_spaces_needed}| ប្រតិបត្តិការ: {total_usd_count}"

        message += f"<pre>{total_data}</pre>\n"

        return message
