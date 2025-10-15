import asyncio
from datetime import datetime

import schedule

from helper import DateUtils, format_custom_report_result
from helper.logger_utils import force_log
from services import CustomReportService


class CustomReportScheduler:
    """Scheduler that executes custom reports at configured times using schedule library"""

    def __init__(self):
        self.custom_report_service = CustomReportService()
        self.is_running = False
        self.scheduled_jobs = {}  # Track scheduled jobs by report_id

    async def start_scheduler(self):
        """Start the custom report scheduler using schedule library"""
        self.is_running = True
        force_log("Custom report scheduler started", "CustomReportScheduler")

        # Initial setup of scheduled jobs
        await self._setup_schedules()

        # Periodically refresh schedules (every 10 minutes) to pick up new/changed reports
        schedule.every(10).minutes.do(lambda: asyncio.create_task(self._setup_schedules()))

        while self.is_running:
            try:
                # Run pending scheduled jobs
                schedule.run_pending()

                # Sleep for 1 second to avoid busy waiting
                await asyncio.sleep(1)

            except Exception as e:
                force_log(f"Error in custom report scheduler loop: {e}", "CustomReportScheduler", "ERROR")
                import traceback
                force_log(f"Traceback: {traceback.format_exc()}", "CustomReportScheduler", "ERROR")
                await asyncio.sleep(60)

    async def stop_scheduler(self):
        """Stop the custom report scheduler"""
        self.is_running = False
        schedule.clear()
        force_log("Custom report scheduler stopped", "CustomReportScheduler")

    async def _setup_schedules(self):
        """Setup scheduled jobs for all reports with scheduling enabled"""
        try:
            # Get all reports with scheduling enabled
            reports = await self.custom_report_service.get_scheduled_reports()

            # Clear existing jobs (except the refresh job)
            for job in list(schedule.jobs):
                if hasattr(job, 'job_func') and job.job_func.keywords.get('is_refresh_job'):
                    continue
                schedule.cancel_job(job)

            self.scheduled_jobs = {}

            for report in reports:
                if not report.schedule_time:
                    continue

                try:
                    # Validate time format
                    datetime.strptime(report.schedule_time, "%H:%M")

                    # Convert ICT time to server's local time for scheduling
                    local_time_str = DateUtils.convert_ict_time_to_local(report.schedule_time)

                    # Create a job for this report at the specified time
                    job = schedule.every().day.at(local_time_str).do(
                        lambda r_id=report.id: asyncio.create_task(
                            self._execute_scheduled_report(r_id)
                        )
                    )

                    self.scheduled_jobs[report.id] = job
                    force_log(
                        f"Scheduled custom report '{report.report_name}' (ID: {report.id}) at {report.schedule_time} ICT ({local_time_str} local)",
                        "CustomReportScheduler"
                    )

                except ValueError:
                    force_log(
                        f"Invalid time format '{report.schedule_time}' for report {report.id}",
                        "CustomReportScheduler",
                        "WARN"
                    )

            force_log(f"Setup {len(self.scheduled_jobs)} scheduled custom reports", "CustomReportScheduler")

        except Exception as e:
            force_log(f"Error in _setup_schedules: {e}", "CustomReportScheduler", "ERROR")
            import traceback
            force_log(f"Traceback: {traceback.format_exc()}", "CustomReportScheduler", "ERROR")

    async def _execute_scheduled_report(self, report_id: int):
        """Execute a scheduled custom report and send to the group"""
        force_log(f"Executing scheduled report ID: {report_id}", "CustomReportScheduler")

        try:
            # Execute the report
            results = await self.custom_report_service.execute_report(report_id)

            # Format the results
            execution_date = DateUtils.now()
            message = format_custom_report_result(
                results.get("report_name", "របាយការណ៍"),
                results,
                execution_date,
                description=results.get("description"),
                trigger_type="auto"
            )

            # Get the report to find the chat_id
            report = await self.custom_report_service.get_report_by_id(report_id)
            if not report:
                force_log(f"Report {report_id} not found", "CustomReportScheduler", "ERROR")
                return

            # Get chat_id from the relationship
            chat_id = report.chat_group.chat_id

            # Send to the group using the appropriate bot
            from services.bot_registry import BotRegistry
            bot_registry = BotRegistry()

            # For BUSINESS groups, use business bot
            business_bot = bot_registry.get_business_bot()

            if business_bot:
                success = await business_bot.send_message(chat_id, message)
                if success:
                    force_log(
                        f"Sent scheduled report '{report.report_name}' to chat {chat_id}",
                        "CustomReportScheduler"
                    )
                else:
                    force_log(
                        f"Failed to send scheduled report '{report.report_name}' to chat {chat_id}, message: {message}",
                        "CustomReportScheduler",
                        "WARN"
                    )
            else:
                force_log("Business bot not available", "CustomReportScheduler", "WARN")

        except Exception as e:
            force_log(
                f"Error executing scheduled report {report_id}: {e}",
                "CustomReportScheduler",
                "ERROR"
            )
            import traceback
            force_log(f"Traceback: {traceback.format_exc()}", "CustomReportScheduler", "ERROR")
