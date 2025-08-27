import asyncio
from datetime import timedelta

import pytz
import schedule
from sqlalchemy import and_

from common.enums.service_package_enum import ServicePackage
from config import get_db_session
from helper import force_log, DateUtils
from models.chat_model import Chat
from models.group_package_model import GroupPackage
from services.telegram_standard_bot_service import TelegramBotService


class PackageExpiryScheduler:
    def __init__(self, standard_bot_service: TelegramBotService, business_bot_service=None, admin_bot_service=None):
        self.standard_bot_service = standard_bot_service
        self.business_bot_service = business_bot_service
        self.admin_bot_service = admin_bot_service
        self.admin_group_id = -4907090942  # Admin group chat ID

    async def notify_expiring_packages(self):
        """
        Find groups with packages expiring in 3 days and send notifications to the groups.
        """
        force_log("Package Expiry Scheduler - Checking for packages expiring in 3 days", "PackageExpiryScheduler")
        try:
            with get_db_session() as session:
                # Calculate the date 3 days from now in Cambodia timezone
                three_days_from_now = DateUtils.now() + timedelta(days=3)
                # Get start and end of that day for comparison
                expiry_date_start = three_days_from_now.replace(hour=0, minute=0, second=0, microsecond=0)
                expiry_date_end = three_days_from_now.replace(hour=23, minute=59, second=59, microsecond=999999)

                # Find packages that expire in exactly 3 days (paid packages only)
                expiring_packages = session.query(GroupPackage).join(Chat).filter(
                    and_(
                        GroupPackage.is_paid == True,
                        GroupPackage.package_end_date >= expiry_date_start,
                        GroupPackage.package_end_date <= expiry_date_end,
                        GroupPackage.package.in_([
                            ServicePackage.BASIC,
                            ServicePackage.STANDARD,
                            ServicePackage.BUSINESS
                        ])
                    )
                ).all()

                # Temporarily disable user group notifications
                # notification_count = 0
                # for group_package in expiring_packages:
                #     try:
                #         chat_group = group_package.chat_group
                #         if not chat_group:
                #             force_log(f"No chat group found for package ID {group_package.id}")
                #             continue
                #
                #         # Format the expiry date for display
                #         expiry_date_str = group_package.package_end_date.strftime("%Y-%m-%d %H:%M")
                #
                #         # Create notification message
                #         message = (
                #             f"⚠️ **Package Expiry Notice** ⚠️\n\n"
                #             f"Dear members,\n\n"
                #             f"Your {group_package.package.value} package is about to expire!\n"
                #             f"📅 **Expiry Date:** {expiry_date_str} (Cambodia Time)\n"
                #             f"⏰ **Time Remaining:** 3 days\n\n"
                #             f"Please renew your package to continue enjoying our services without interruption.\n\n"
                #             f"Contact support for renewal assistance."
                #         )
                #
                #         # Choose the appropriate bot service based on package type
                #         if group_package.package == ServicePackage.BUSINESS:
                #             # Use business bot for BUSINESS packages
                #             if self.business_bot_service:
                #                 success = await self.business_bot_service.send_message(chat_group.chat_id, message)
                #                 if success:
                #                     notification_count += 1
                #                     force_log(
                #                         f"Sent expiry notification via business bot to group {chat_group.chat_id} "
                #                         f"(Package: {group_package.package.value}, "
                #                         f"Expires: {expiry_date_str})",
                #                         "package_expiry_scheduler"
                #                     )
                #                 else:
                #                     force_log(
                #                         f"Failed to send notification via business bot to group {chat_group.chat_id}",
                #                         "package_expiry_scheduler"
                #                     )
                #             else:
                #                 force_log("Business bot service not available for BUSINESS package notification", "package_expiry_scheduler")
                #         else:
                #             # Use standard bot for BASIC and STANDARD packages
                #             await self.standard_bot_service.send_message_to_chat(chat_group.chat_id, message)
                #             notification_count += 1
                #             force_log(
                #                 f"Sent expiry notification via standard bot to group {chat_group.chat_id} "
                #                 f"(Package: {group_package.package.value}, "
                #                 f"Expires: {expiry_date_str})",
                #                 "package_expiry_scheduler"
                #             )
                #
                #     except Exception as e:
                #         force_log(
                #             f"Failed to send expiry notification to group {group_package.chat_group_id}: {str(e)}",
                #             "package_expiry_scheduler"
                #         )

                if expiring_packages:
                    force_log(f"Found {len(expiring_packages)} packages expiring in 3 days", "PackageExpiryScheduler")
                    # Send admin alert only
                    await self.send_admin_alert(expiring_packages)
                else:
                    force_log("No packages found expiring in 3 days", "PackageExpiryScheduler")

        except Exception as e:
            force_log(f"Error in notify_expiring_packages: {str(e)}", "PackageExpiryScheduler", "ERROR")

    async def send_admin_alert(self, expiring_packages):
        """
        Send an alert to the admin group about packages expiring in 3 days
        
        Args:
            expiring_packages: List of GroupPackage objects that are expiring
        """
        if not self.admin_bot_service or not expiring_packages:
            return
            
        try:
            # Create admin alert message
            current_time = DateUtils.now().strftime("%Y-%m-%d %H:%M")
            
            admin_message = f"🚨 **ADMIN ALERT - Package Expiry Notifications** 🚨\n\n"
            admin_message += f"📅 **Alert Time:** {current_time} (Cambodia Time)\n"
            admin_message += f"⚠️ **Packages expiring in 3 days:** {len(expiring_packages)}\n\n"
            admin_message += "📋 **Details:**\n"
            
            for i, group_package in enumerate(expiring_packages, 1):
                chat_group = group_package.chat_group
                expiry_date_str = group_package.package_end_date.strftime("%Y-%m-%d %H:%M")
                group_name = chat_group.group_name if chat_group else "Unknown Group"
                
                admin_message += f"{i}. **{group_name}**\n"
                admin_message += f"   📊 Package: {group_package.package.value}\n"
                admin_message += f"   🆔 Chat ID: {group_package.chat_group_id}\n"
                admin_message += f"   ⏰ Expires: {expiry_date_str}\n"
                admin_message += f"   💰 Amount Paid: ${group_package.amount_paid or 'N/A'}\n\n"
                
                # Limit message length to avoid Telegram limits
                if len(admin_message) > 3500:  # Leave room for closing message
                    admin_message += f"... and {len(expiring_packages) - i} more packages\n\n"
                    break
            
            admin_message += "🔔 **Action Required:**\n"
            admin_message += "• Follow up with customers for renewals\n"
            admin_message += "• Prepare for potential downgrades if not renewed\n"
            admin_message += "• Monitor payment notifications\n\n"
            admin_message += "📊 Generated by Package Expiry Scheduler"
            
            # Send admin alert
            success = await self.admin_bot_service.send_message(self.admin_group_id, admin_message)
            
            if success:
                force_log(f"Successfully sent admin alert for {len(expiring_packages)} expiring packages", "PackageExpiryScheduler")
            else:
                force_log("Failed to send admin alert", "PackageExpiryScheduler", "WARN")
                
        except Exception as e:
            force_log(f"Error sending admin alert: {str(e)}", "PackageExpiryScheduler", "ERROR")

    async def start_scheduler(self):
        """
        Start the scheduler to run the package expiry notification job.
        """
        # Schedule the job to run daily at 10:00 AM Cambodia time
        cambodia_tz = pytz.timezone('Asia/Phnom_Penh')
        schedule.every().day.at("10:00", cambodia_tz).do(
            lambda: asyncio.create_task(self.notify_expiring_packages())
        )

        force_log("Package expiry scheduler started. Job will run daily at 10:00 AM Cambodia time (Asia/Phnom_Penh)", "PackageExpiryScheduler")

        try:
            while True:
                schedule.run_pending()
                await asyncio.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            force_log("Package expiry scheduler stopped by user", "PackageExpiryScheduler")
        except Exception as e:
            force_log(f"Error in scheduler: {str(e)}", "PackageExpiryScheduler", "ERROR")