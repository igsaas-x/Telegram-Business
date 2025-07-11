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
            buttons.append([("📊 វេននេះ", "this_shift")])

        buttons.extend([
            [("📈 វេនមុន", "previous_shifts")],
            [("🔄 គ្រប់គ្រងវេន", "shift_management")],
            [("⚙️ ការកំណត់អាជីវកម្ម", "business_settings")],
            [("📞 ជំនួយ", "support")]
        ])

        message = f"""
🏢 ផ្ទាំងគ្រប់គ្រងអាជីវកម្ម

{shift_summary}

🔧 សកម្មភាពរហ័ស:
ជ្រើសរើសជម្រើសខាងក្រោមដើម្បីគ្រប់គ្រងប្រតិបត្តិការវេនរបស់អ្នក។
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
✅ ការចុះឈ្មោះអាជីវកម្មបានជោគជ័យ!

🏢 ជជែករបស់អ្នកត្រូវបានចុះឈ្មោះសម្រាប់សេវាអាជីវកម្ម។
📊 ការវិភាគកម្រិតខ្ពស់និងការគ្រប់គ្រងវេនឥឡូវនេះត្រូវបានបើក។
💼 អ្នកអាចចូលប្រើលក្ខណៈពិសេសអាជីវកម្មតាមរយៈម៉ឺនុយ។

វាយ /menu ដើម្បីចាប់ផ្តើមជាមួយនឹងផ្ទាំងគ្រប់គ្រងអាជីវកម្មរបស់អ្នក។
            """
        else:
            response = f"❌ Business registration failed: {message}"

        await event.respond(response)

    async def get_shift_summary(self, chat_id: str, current_shift) -> str:
        """Get shift-based summary"""
        try:
            if not current_shift:
                return """
📊 ស្ថានភាពវេន:
🔴 គ្មានវេនសកម្ម

💡 គន្លឹះ: ចាប់ផ្តើមវេនថ្មីដើម្បីចាប់ផ្តើមតាមដានចំណូល។
ប្រើការគ្រប់គ្រងវេនដើម្បីចាប់ផ្តើមវេនថ្មី។
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
                f"📊 វេនបច្ចុប្បន្ន: #{current_shift.number}",
                f"🟢 ស្ថានភាព: សកម្ម",
                f"⏰ ចាប់ផ្តើម: {current_shift.start_time.strftime('%Y-%m-%d %H:%M')}",
                f"⏱️ រយៈពេល: {hours}ម៉ោង {minutes}នាទី",
                f"💰 ចំណូល: ${shift_summary['total_amount']:,.2f}",
                f"📝 ប្រតិបត្តិការ: {shift_summary['transaction_count']}"
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
📊 វេនបច្ចុប្បន្ន

🔴 គ្មានវេនសកម្មកំពុងដំណើរការ។

💡 គន្លឹះ: ចាប់ផ្តើមវេនថ្មីដើម្បីចាប់ផ្តើមតាមដានចំណូល។
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
📊 វេនបច្ចុប្បន្ន #{current_shift.number}

🟢 ស្ថានភាព: សកម្ម
⏰ ចាប់ផ្តើម: {current_shift.start_time.strftime('%Y-%m-%d %H:%M')}
⏱️ រយៈពេល: {hours}ម៉ោង {minutes}នាទី

💰 សង្ខេបចំណូល:
• សរុប: ${shift_summary['total_amount']:,.2f}
• ប្រតិបត្តិការ: {shift_summary['transaction_count']}

💱 ការចែករូបិយប័ណ្ណ:
{currency_text if currency_text else '• មិនទាន់មានប្រតិបត្តិការទេ'}

⏰ ម៉ោងបញ្ចប់: បច្ចុប្បន្ន (វេនកំពុងសកម្ម)
                """

            if current_shift:
                buttons = [
                    [("🛑 បិទវេនបច្ចុប្បន្ន", "close_shift")],
                    [("🔙 ត្រឡប់ទៅមីនុយ", "back_to_menu")]
                ]
            else:
                buttons = [[("🔙 ត្រឡប់ទៅមីនុយ", "back_to_menu")]]

        except Exception as e:
            logger.error(f"Error showing current shift: {e}")
            message = "❌ Unable to load current shift data. Please try again."
            buttons = [[("🔙 ត្រឡប់ទៅមីនុយ", "back_to_menu")]]

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
                buttons = [[("🔙 ត្រឡប់ទៅមីនុយ", "back_to_menu")]]
            else:
                message = "📈 វេនមុន (ចំណួរចុងក្រោយ 3)\n\n"

                buttons = []
                for shift in recent_shifts:
                    shift_summary = await self.shift_service.get_shift_income_summary(shift.id)
                    duration = shift.end_time - shift.start_time
                    hours = int(duration.total_seconds() // 3600)
                    minutes = int((duration.total_seconds() % 3600) // 60)

                    shift_text = f"""
📊 វេន #{shift.number}
⏰ {shift.start_time.strftime('%m/%d %H:%M')} - {shift.end_time.strftime('%m/%d %H:%M')} ({hours}ម៉ោង {minutes}នាទី)
💰 ${shift_summary['total_amount']:,.2f} ({shift_summary['transaction_count']} ប្រតិបត្តិការ)
                    """
                    message += shift_text

                    # Add button for each shift
                    buttons.append([(f"Shift #{shift.number} Details", f"shift_{shift.id}")])

                buttons.append([("📅 ថ្ងៃផ្សេងទៀត", "other_days")])
                buttons.append([("🔙 Back to Menu", "back_to_menu")])

        except Exception as e:
            logger.error(f"Error showing previous shifts: {e}")
            message = "❌ Unable to load previous shifts. Please try again."
            buttons = [[("🔙 ត្រឡប់ទៅមីនុយ", "back_to_menu")]]

        await event.edit(message, buttons=buttons)

    async def show_analytics(self, event):
        """Show business analytics"""
        message = """
📈 ការវិភាគអាជីវកម្ម

🔍 លក្ខណៈពិសេសការវិភាគកម្រិតខ្ពស់កំពុងមកដល់ថ្ងៃខាងមុខ:
• និន្នាការចំណូលនិងការក្រធាធង
• រូបមន្តប្រតិបត្តិការអតិថិជន
• ការវិភាគម៉ោងច្រើន
• របាយការណ៍ប្រចាំខែនិងរយៈពេល 3 ខែ
• ការប្រាប់ព្រាប់ការអនុវត្ត

💼 មានបច្ចុប្បន្ន:
• តាមដានចំណូលប្រចាំថ្ងៃ
• ការតាមដានប្រតិបត្តិការ
• ការគ្រប់គ្រងវេន
• សង្ខេបមូលដ្ឋាន

📞 ទាក់ទងការគាំទ្រសម្រាប់សំណើរការវិភាគផ្ទាល់ខ្លួន។
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
🔄 ការគ្រប់គ្រងវេន

🟢 វេនបច្ចុប្បន្ន: #{current_shift.number}
⏰ ចាប់ផ្តើម: {current_shift.start_time.strftime('%Y-%m-%d %H:%M')}
⏱️ រយៈពេល: {hours}ម៉ោង {minutes}នាទី

⚙️ សកម្មភាពដែលមាន:
• បិទវេនបច្ចុប្បន្ន
• មើលសម្របសម្រួលវេន
• តាមដានការអនុវត្តវេន
                """

                buttons = [
                    [("🛑 បិទវេនបច្ចុប្បន្ន", "close_shift")],
                    [("📊 មើលវេននេះ", "this_shift")],
                    [("🔙 Back to Menu", "back_to_menu")]
                ]
            else:
                message = """
🔄 ការគ្រប់គ្រងវេន

🔴 ស្ថានភាព: គ្មានវេនសកម្ម

⚙️ សកម្មភាពដែលមាន:
• ចាប់ផ្តើមវេនថ្មី
• មើលវេនមុន
• គ្រប់គ្រងការកំណត់វេន

💡 គន្លឹះ: ចាប់ផ្តើមវេនដើម្បីចាប់ផ្តើមតាមដានចំណូលតាមរយៈពេលការងារ។
                """

                buttons = [
                    [("▶️ ចាប់ផ្តើមវេនថ្មី", "start_shift")],
                    [("📈 Previous Shifts", "previous_shifts")],
                    [("🔙 Back to Menu", "back_to_menu")]
                ]

        except Exception as e:
            logger.error(f"Error showing shift management: {e}")
            message = "❌ Unable to load shift management. Please try again."
            buttons = [[("🔙 ត្រឡប់ទៅមីនុយ", "back_to_menu")]]

        await event.edit(message, buttons=buttons)

    async def show_specific_shift(self, event, data):
        """Show details for a specific shift"""
        try:
            shift_id = int(data.split('_')[1])
            shift = await self.shift_service.get_shift_by_id(shift_id)

            if not shift:
                message = "❌ Shift not found."
                buttons = [[("🔙 ត្រឡប់ទៅមីនុយ", "back_to_menu")]]
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
            buttons = [[("🔙 ត្រឡប់ទៅមីនុយ", "back_to_menu")]]

        await event.edit(message, buttons=buttons)

    async def start_new_shift(self, event):
        """Start a new shift"""
        chat_id = str(event.chat_id)

        try:
            # Check if there's already an active shift
            current_shift = await self.shift_service.get_current_shift(chat_id)

            if current_shift:
                message = f"""
⚠️ **Cannot ចាប់ផ្តើមវេនថ្មី**

There is already an active shift running:
📊 Shift #{current_shift.number}
⏰ Started: {current_shift.start_time.strftime('%Y-%m-%d %H:%M')}

💡 **Tip:** Close the current shift before starting a new one.
                """

                buttons = [
                    [("🛑 បិទវេនបច្ចុប្បន្ន", "close_shift")],
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
                    [("📊 មើលវេននេះ", "this_shift")],
                    [("🔙 Back to Menu", "back_to_menu")]
                ]

        except Exception as e:
            logger.error(f"Error starting new shift: {e}")
            message = "❌ Unable to start new shift. Please try again."
            buttons = [[("🔙 ត្រឡប់ទៅមីនុយ", "back_to_menu")]]

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
                    [("▶️ ចាប់ផ្តើមវេនថ្មី", "start_shift")],
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
                        [("▶️ ចាប់ផ្តើមវេនថ្មី", "start_shift")],
                        [("📈 View All Shifts", "previous_shifts")],
                        [("🔙 Back to Menu", "back_to_menu")]
                    ]
                else:
                    message = "❌ Failed to close shift. Please try again."
                    buttons = [[("🔙 ត្រឡប់ទៅមីនុយ", "back_to_menu")]]

        except Exception as e:
            logger.error(f"Error closing shift: {e}")
            message = "❌ Unable to close shift. Please try again."
            buttons = [[("🔙 ត្រឡប់ទៅមីនុយ", "back_to_menu")]]

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
