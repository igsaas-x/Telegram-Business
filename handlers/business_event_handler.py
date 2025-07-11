import logging

from models import ChatService, IncomeService, UserService, ShiftService
from models.user_model import User
from .client_command_handler import CommandHandler

logger = logging.getLogger(__name__)


class BusinessEventHandler:
    """
    Specialized event handler for autosum_business bot with different business logic
    """

    def __init__(self):
        self.command_handler = CommandHandler()
        self.chat_service = ChatService()
        self.income_service = IncomeService()
        self.shift_service = ShiftService()

    async def menu(self, event):
        """Business-specific menu handler with shift-based operations"""
        # Check if chat is activated and trial status
        chat = await self.chat_service.get_chat_by_chat_id(str(event.chat_id))
        if not chat:
            # Auto-register for business bot
            try:
                sender = await event.get_sender()

                if not sender or not hasattr(sender, 'id') or sender.id is None:
                    message = "⚠️ Business Registration failed: You must be a non-anonymous user to register this chat for business services."
                    await event.respond(message)
                    return

                # Create user for business service
                user_service = UserService()
                user = await user_service.create_user(sender)

                # Register with business-specific settings
                await self.register_business(event, user)

                # Refresh chat information after registration
                chat = await self.chat_service.get_chat_by_chat_id(str(event.chat_id))

                if not chat:
                    return

            except Exception as e:
                logger.error(f"Error during business auto-registration: {e}")
                message = "⚠️ Business auto-registration failed. Please contact support."
                await event.respond(message)
                return

        # Business-specific menu with shift focus
        chat_id = str(event.chat_id)

        # Get current shift status
        current_shift = await self.shift_service.get_current_shift(chat_id)
        shift_summary = await self.get_shift_summary(chat_id, current_shift)

        # Create shift-based menu buttons
        buttons = []

        if current_shift:
            buttons.append([("📊 This Shift", "this_shift")])

        buttons.extend([
            [("📈 Previous Shifts", "previous_shifts")],
            [("🔄 Shift Management", "shift_management")],
            [("⚙️ Business Settings", "business_settings")],
            [("📞 Support", "support")]
        ])

        message = f"""
🏢 **Business Dashboard**

{shift_summary}

🔧 **Quick Actions:**
Choose an option below to manage your shift operations.
        """

        await event.respond(message, buttons=buttons)

    async def register_business(self, event, user: User):
        """Register chat for business services with special configuration"""
        chat_id = str(event.chat_id)
        chat_title = "Business Chat"

        # Try to get chat title
        try:
            if hasattr(event, 'chat') and event.chat:
                chat_title = getattr(event.chat, 'title', 'Business Chat')
        except:
            pass

        success, message = await self.chat_service.register_chat_id(
            chat_id, f"[BUSINESS] {chat_title}", user
        )

        if success:
            # Enable shift by default for business chats
            await self.chat_service.update_chat_enable_shift(chat_id, True)

            response = f"""
✅ **Business Registration Successful!**

🏢 Your chat has been registered for business services.
📊 Advanced analytics and shift management are now enabled.
💼 You can access business features through the menu.

Type /menu to get started with your business dashboard.
            """
        else:
            response = f"❌ Business registration failed: {message}"

        await event.respond(response)

    async def get_shift_summary(self, chat_id: str, current_shift) -> str:
        """Get shift-based summary"""
        try:
            if not current_shift:
                return """
📊 **Shift Status:**
🔴 No active shift

💡 **Tip:** Start a new shift to begin tracking revenue.
Use Shift Management to start a new shift.
                """

            # Get income data for current shift
            shift_summary = await self.shift_service.get_shift_income_summary(current_shift.id)

            # Calculate shift duration
            from datetime import datetime
            now = datetime.now()
            duration = now - current_shift.start_time
            hours = int(duration.total_seconds() // 3600)
            minutes = int((duration.total_seconds() % 3600) // 60)

            summary_parts = [
                f"📊 **Current Shift:** #{current_shift.number}",
                f"🟢 **Status:** Active",
                f"⏰ **Started:** {current_shift.start_time.strftime('%Y-%m-%d %H:%M')}",
                f"⏱️ **Duration:** {hours}h {minutes}m",
                f"💰 **Revenue:** ${shift_summary['total_amount']:,.2f}",
                f"📝 **Transactions:** {shift_summary['transaction_count']}"
            ]

            return "\n".join(summary_parts)

        except Exception as e:
            logger.error(f"Error getting shift summary: {e}")
            return "📊 Shift summary unavailable"

    async def handle_business_callback(self, event):
        """Handle business-specific callback queries"""
        data = event.data.decode('utf-8')
        chat_id = str(event.chat_id)

        if data == "this_shift":
            await self.show_this_shift(event)
        elif data == "previous_shifts":
            await self.show_previous_shifts(event)
        elif data == "shift_management":
            await self.show_shift_management(event)
        elif data == "business_settings":
            await self.show_business_settings(event)
        elif data == "support":
            await self.show_support(event)
        elif data.startswith("shift_"):
            await self.show_specific_shift(event, data)
        elif data == "start_shift":
            await self.start_new_shift(event)
        elif data == "close_shift":
            await self.close_current_shift(event)
        else:
            # Fallback to regular command handler
            await self.command_handler.handle_callback_query(event)

    async def show_this_shift(self, event):
        """Show current shift details"""
        chat_id = str(event.chat_id)

        try:
            current_shift = await self.shift_service.get_current_shift(chat_id)

            if not current_shift:
                message = """
📊 **Current Shift**

🔴 No active shift running.

💡 **Tip:** Start a new shift to begin tracking revenue.
                """
            else:
                shift_summary = await self.shift_service.get_shift_income_summary(current_shift.id)

                # Calculate duration
                from datetime import datetime
                now = datetime.now()
                duration = now - current_shift.start_time
                hours = int(duration.total_seconds() // 3600)
                minutes = int((duration.total_seconds() % 3600) // 60)

                # Currency breakdown
                currency_text = ""
                for currency, data in shift_summary['currencies'].items():
                    currency_text += f"• {currency}: ${data['amount']:,.2f} ({data['count']} transactions)\n"

                message = f"""
📊 **Current Shift #{current_shift.number}**

🟢 **Status:** Active
⏰ **Started:** {current_shift.start_time.strftime('%Y-%m-%d %H:%M')}
⏱️ **Duration:** {hours}h {minutes}m

💰 **Revenue Summary:**
• Total: ${shift_summary['total_amount']:,.2f}
• Transactions: {shift_summary['transaction_count']}

💱 **Currency Breakdown:**
{currency_text if currency_text else '• No transactions yet'}

⏰ **End Time:** Current (shift is active)
                """

            buttons = [[("🔙 Back to Menu", "back_to_menu")]]

        except Exception as e:
            logger.error(f"Error showing current shift: {e}")
            message = "❌ Unable to load current shift data. Please try again."
            buttons = [[("🔙 Back to Menu", "back_to_menu")]]

        await event.edit(message, buttons=buttons)

    async def show_previous_shifts(self, event):
        """Show list of previous shifts"""
        chat_id = str(event.chat_id)

        try:
            recent_shifts = await self.shift_service.get_recent_closed_shifts(chat_id, 3)

            if not recent_shifts:
                message = """
📈 **Previous Shifts**

🔴 No completed shifts found.

💡 **Tip:** Previous shifts will appear here after you close them.
                """
                buttons = [[("🔙 Back to Menu", "back_to_menu")]]
            else:
                message = "📈 **Previous Shifts (Recent 3)**\n\n"

                buttons = []
                for shift in recent_shifts:
                    shift_summary = await self.shift_service.get_shift_income_summary(shift.id)
                    duration = shift.end_time - shift.start_time
                    hours = int(duration.total_seconds() // 3600)
                    minutes = int((duration.total_seconds() % 3600) // 60)

                    shift_text = f"""
📊 **Shift #{shift.number}**
⏰ {shift.start_time.strftime('%m/%d %H:%M')} - {shift.end_time.strftime('%m/%d %H:%M')} ({hours}h {minutes}m)
💰 ${shift_summary['total_amount']:,.2f} ({shift_summary['transaction_count']} transactions)
                    """
                    message += shift_text

                    # Add button for each shift
                    buttons.append([(f"Shift #{shift.number} Details", f"shift_{shift.id}")])

                buttons.append([("📅 Other Days", "other_days")])
                buttons.append([("🔙 Back to Menu", "back_to_menu")])

        except Exception as e:
            logger.error(f"Error showing previous shifts: {e}")
            message = "❌ Unable to load previous shifts. Please try again."
            buttons = [[("🔙 Back to Menu", "back_to_menu")]]

        await event.edit(message, buttons=buttons)

    async def show_analytics(self, event):
        """Show business analytics"""
        message = """
📈 **Business Analytics**

🔍 **Advanced analytics features coming soon:**
• Revenue trends and forecasting
• Customer transaction patterns
• Peak hour analysis
• Monthly/quarterly reports
• Performance comparisons

💼 **Currently Available:**
• Daily revenue tracking
• Transaction monitoring
• Shift management
• Basic summaries

📞 Contact support for custom analytics requests.
        """

        buttons = [[("🔙 Back to Menu", "back_to_menu")]]
        await event.edit(message, buttons=buttons)

    async def show_shift_management(self, event):
        """Show shift management options"""
        chat_id = str(event.chat_id)

        try:
            current_shift = await self.shift_service.get_current_shift(chat_id)

            if current_shift:
                from datetime import datetime
                duration = datetime.now() - current_shift.start_time
                hours = int(duration.total_seconds() // 3600)
                minutes = int((duration.total_seconds() % 3600) // 60)

                message = f"""
🔄 **Shift Management**

🟢 **Current Shift:** #{current_shift.number}
⏰ **Started:** {current_shift.start_time.strftime('%Y-%m-%d %H:%M')}
⏱️ **Duration:** {hours}h {minutes}m

⚙️ **Available Actions:**
• Close current shift
• View shift details
• Monitor shift performance
                """

                buttons = [
                    [("🛑 Close Current Shift", "close_shift")],
                    [("📊 View This Shift", "this_shift")],
                    [("🔙 Back to Menu", "back_to_menu")]
                ]
            else:
                message = """
🔄 **Shift Management**

🔴 **Status:** No active shift

⚙️ **Available Actions:**
• Start a new shift
• View previous shifts
• Manage shift settings

💡 **Tip:** Start a shift to begin tracking revenue by work periods.
                """

                buttons = [
                    [("▶️ Start New Shift", "start_shift")],
                    [("📈 Previous Shifts", "previous_shifts")],
                    [("🔙 Back to Menu", "back_to_menu")]
                ]

        except Exception as e:
            logger.error(f"Error showing shift management: {e}")
            message = "❌ Unable to load shift management. Please try again."
            buttons = [[("🔙 Back to Menu", "back_to_menu")]]

        await event.edit(message, buttons=buttons)

    async def show_specific_shift(self, event, data):
        """Show details for a specific shift"""
        try:
            shift_id = int(data.split('_')[1])
            shift = await self.shift_service.get_shift_by_id(shift_id)

            if not shift:
                message = "❌ Shift not found."
                buttons = [[("🔙 Back to Menu", "back_to_menu")]]
            else:
                shift_summary = await self.shift_service.get_shift_income_summary(shift.id)

                # Calculate duration
                from datetime import datetime
                if shift.end_time:
                    duration = shift.end_time - shift.start_time
                    end_text = shift.end_time.strftime('%Y-%m-%d %H:%M')
                    status = "🔴 Closed"
                else:
                    duration = datetime.now() - shift.start_time
                    end_text = "Current (shift active)"
                    status = "🟢 Active"

                hours = int(duration.total_seconds() // 3600)
                minutes = int((duration.total_seconds() % 3600) // 60)

                # Currency breakdown
                currency_text = ""
                for currency, data in shift_summary['currencies'].items():
                    currency_text += f"• {currency}: ${data['amount']:,.2f} ({data['count']} transactions)\n"

                message = f"""
📊 **Shift #{shift.number} Details**

{status}
⏰ **Start:** {shift.start_time.strftime('%Y-%m-%d %H:%M')}
⏱️ **End:** {end_text}
⏲️ **Duration:** {hours}h {minutes}m

💰 **Revenue Summary:**
• Total: ${shift_summary['total_amount']:,.2f}
• Transactions: {shift_summary['transaction_count']}

💱 **Currency Breakdown:**
{currency_text if currency_text else '• No transactions recorded'}
                """

                buttons = [
                    [("📈 Previous Shifts", "previous_shifts")],
                    [("🔙 Back to Menu", "back_to_menu")]
                ]

        except Exception as e:
            logger.error(f"Error showing specific shift: {e}")
            message = "❌ Unable to load shift details. Please try again."
            buttons = [[("🔙 Back to Menu", "back_to_menu")]]

        await event.edit(message, buttons=buttons)

    async def start_new_shift(self, event):
        """Start a new shift"""
        chat_id = str(event.chat_id)

        try:
            # Check if there's already an active shift
            current_shift = await self.shift_service.get_current_shift(chat_id)

            if current_shift:
                message = f"""
⚠️ **Cannot Start New Shift**

There is already an active shift running:
📊 Shift #{current_shift.number}
⏰ Started: {current_shift.start_time.strftime('%Y-%m-%d %H:%M')}

💡 **Tip:** Close the current shift before starting a new one.
                """

                buttons = [
                    [("🛑 Close Current Shift", "close_shift")],
                    [("🔙 Back to Menu", "back_to_menu")]
                ]
            else:
                # Create new shift
                new_shift = await self.shift_service.create_shift(chat_id)

                message = f"""
✅ **New Shift Started!**

📊 **Shift #{new_shift.number}**
⏰ **Started:** {new_shift.start_time.strftime('%Y-%m-%d %H:%M')}
🟢 **Status:** Active

💡 **Tip:** All revenue will now be tracked under this shift.
Use Shift Management to close this shift when done.
                """

                buttons = [
                    [("📊 View This Shift", "this_shift")],
                    [("🔙 Back to Menu", "back_to_menu")]
                ]

        except Exception as e:
            logger.error(f"Error starting new shift: {e}")
            message = "❌ Unable to start new shift. Please try again."
            buttons = [[("🔙 Back to Menu", "back_to_menu")]]

        await event.edit(message, buttons=buttons)

    async def close_current_shift(self, event):
        """Close the current active shift"""
        chat_id = str(event.chat_id)

        try:
            current_shift = await self.shift_service.get_current_shift(chat_id)

            if not current_shift:
                message = """
⚠️ **No Active Shift**

There is no active shift to close.

💡 **Tip:** Start a new shift to begin tracking revenue.
                """

                buttons = [
                    [("▶️ Start New Shift", "start_shift")],
                    [("🔙 Back to Menu", "back_to_menu")]
                ]
            else:
                # Close the shift
                closed_shift = await self.shift_service.close_shift(current_shift.id)

                if closed_shift:
                    # Get final summary
                    shift_summary = await self.shift_service.get_shift_income_summary(closed_shift.id)
                    duration = closed_shift.end_time - closed_shift.start_time
                    hours = int(duration.total_seconds() // 3600)
                    minutes = int((duration.total_seconds() % 3600) // 60)

                    message = f"""
✅ **Shift Closed Successfully!**

📊 **Shift #{closed_shift.number} Summary:**
⏰ **Started:** {closed_shift.start_time.strftime('%Y-%m-%d %H:%M')}
⏱️ **Ended:** {closed_shift.end_time.strftime('%Y-%m-%d %H:%M')}
⏲️ **Duration:** {hours}h {minutes}m

💰 **Final Results:**
• Total Revenue: ${shift_summary['total_amount']:,.2f}
• Transactions: {shift_summary['transaction_count']}

🎉 **Great work!**
                    """

                    buttons = [
                        [("▶️ Start New Shift", "start_shift")],
                        [("📈 View All Shifts", "previous_shifts")],
                        [("🔙 Back to Menu", "back_to_menu")]
                    ]
                else:
                    message = "❌ Failed to close shift. Please try again."
                    buttons = [[("🔙 Back to Menu", "back_to_menu")]]

        except Exception as e:
            logger.error(f"Error closing shift: {e}")
            message = "❌ Unable to close shift. Please try again."
            buttons = [[("🔙 Back to Menu", "back_to_menu")]]

        await event.edit(message, buttons=buttons)

    async def show_business_settings(self, event):
        """Show business settings"""
        message = """
⚙️ **Business Settings**

🔧 **Configuration Options:**
• Enable/disable shift tracking
• Set currency preferences
• Configure report frequency
• Notification settings
• Data export options

🔒 **Account Management:**
• Business profile settings
• User permissions
• Backup configurations

📱 **Contact admin to modify these settings.**
        """

        buttons = [[("🔙 Back to Menu", "back_to_menu")]]
        await event.edit(message, buttons=buttons)

    async def show_support(self, event):
        """Show support information"""
        message = """
📞 **Business Support**

🆘 **Need Help?**
• Technical issues with the bot
• Questions about business features
• Custom reporting requests
• Account management

📧 **Contact Methods:**
• In-app support: Reply to this message
• Email: business@yourcompany.com
• Phone: +1-XXX-XXX-XXXX

⏰ **Support Hours:**
Monday - Friday: 9:00 AM - 6:00 PM
Saturday: 10:00 AM - 2:00 PM
Sunday: Closed

🚀 **Premium Support:** Available for business accounts
        """

        buttons = [[("🔙 Back to Menu", "back_to_menu")]]
        await event.edit(message, buttons=buttons)
