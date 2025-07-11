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
        """Business-specific menu handler"""
        # Check if chat is activated and trial status
        chat = await self.chat_service.get_chat_by_chat_id(event.chat_id)
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
                chat = await self.chat_service.get_chat_by_chat_id(event.chat_id)

                if not chat:
                    return

            except Exception as e:
                logger.error(f"Error during business auto-registration: {e}")
                message = "⚠️ Business auto-registration failed. Please contact support."
                await event.respond(message)
                return

        # Create menu buttons based on shift status
        chat_id = event.chat_id
        current_shift = await self.shift_service.get_current_shift(chat_id)

        if current_shift:
            buttons = [
                [("📊 របាយការណ៍វេននេះ", "current_shift_report")],
                [("📈 របាយការណ៍វេនមុន", "previous_shift_report")],
                [("📅 របាយការណ៍ថ្ងៃផ្សេង", "other_days_report")],
                [("🛑 បិទបញ្ជី", "close_shift")],
                [("❌ បិទ", "close_menu")]
            ]
        else:
            buttons = [
                [("📈 របាយការណ៍វេនមុន", "previous_shift_report")],
                [("📅 របាយការណ៍ថ្ងៃផ្សេង", "other_days_report")],
                [("❌ បិទ", "close_menu")]
            ]

        message = f"""
ជ្រើសរើសជម្រើសខាងក្រោម
        """

        # Check if this is a callback query (edit existing message) or new message (respond)
        if hasattr(event, 'data') and hasattr(event, 'edit'):
            # This is a callback query, edit the existing message
            await event.edit(message, buttons=buttons)
        else:
            # This is a regular message, respond with new message
            await event.respond(message, buttons=buttons)

    async def register_business(self, event, user: User):
        """Register chat for business services with special configuration"""
        chat_id = int(event.chat_id)
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
            response = f"""
✅ ការចុះឈ្មោះអាជីវកម្មបានជោគជ័យ!

🏢 ជជែករបស់អ្នកត្រូវបានចុះឈ្មោះសម្រាប់សេវាអាជីវកម្ម។
📊 ការវិភាគកម្រិតខ្ពស់ឥឡូវនេះត្រូវបានបើក។
💼 អ្នកអាចចូលប្រើលក្ខណៈពិសេសអាជីវកម្មតាមរយៈម៉ឺនុយ។

វាយ /menu ដើម្បីចាប់ផ្តើមជាមួយនឹងផ្ទាំងគ្រប់គ្រងអាជីវកម្មរបស់អ្នក។
            """
        else:
            response = f"❌ Business registration failed: {message}"

        await event.respond(response)

    async def handle_business_callback(self, event):
        """Handle business-specific callback queries"""
        data = event.data.decode('utf-8')
        logger.error(f"CRITICAL DEBUG: handle_business_callback received data: {data}")

        if data == "current_shift_report":
            logger.error(f"CRITICAL DEBUG: Calling show_current_shift_report")
            await self.show_current_shift_report(event)
        elif data == "previous_shift_report":
            await self.show_previous_shift_report(event)
        elif data == "other_days_report":
            await self.show_other_days_report(event)
        elif data == "close_shift":
            await self.close_current_shift(event)
        elif data == "close_menu":
            await self.close_menu(event)
        elif data == "back_to_menu":
            await self.menu(event)
        elif data.startswith("shift_"):
            await self.show_specific_shift_report(event, data)
        elif data.startswith("date_"):
            await self.show_date_shifts(event, data)
        else:
            # Fallback to regular command handler
            await self.command_handler.handle_callback_query(event)

    async def show_current_shift_report(self, event):
        """Show current shift report"""
        global DateUtils
        chat_id = int(event.chat_id)
        logger.error(f"CRITICAL DEBUG: show_current_shift_report called for chat_id: {chat_id}")

        try:
            current_shift = await self.shift_service.get_current_shift(chat_id)
            logger.info(f"Current shift for chat_id {chat_id}: {current_shift}")

            if not current_shift:
                message = """
📊 របាយការណ៍វេនបច្ចុប្បន្ន

🔴 គ្មានវេនសកម្មកំពុងដំណើរការ។

💡 វេនថ្មីនឹងត្រូវបានបង្កើតដោយស្វ័យប្រវត្តិនៅពេលមានប្រតិបត្តិការថ្មី។
                """
                buttons = [[("🔙 ត្រឡប់ទៅមីនុយ", "back_to_menu")]]
            else:
                shift_summary = await self.shift_service.get_shift_income_summary(current_shift.id)

                # Calculate duration - simplified approach first
                try:
                    now = DateUtils.now()
                    logger.error(f"DEBUG: Now: {now}, Start time: {current_shift.start_time}")
                    duration = now - current_shift.start_time
                    logger.error(f"DEBUG: Duration: {duration}")
                    total_seconds = abs(duration.total_seconds())
                    hours = int(total_seconds // 3600)
                    minutes = int((total_seconds % 3600) // 60)
                    logger.error(f"DEBUG: Hours: {hours}, Minutes: {minutes}")
                except Exception as e:
                    logger.error(f"Error in duration calculation: {e}")
                    # Fallback to simple calculation
                    from datetime import datetime
                    now = datetime.now()
                    
                    duration = now - current_shift.start_time
                    total_seconds = abs(duration.total_seconds())
                    hours = int(total_seconds // 3600)
                    minutes = int((total_seconds % 3600) // 60)

                # Currency breakdown
                currency_text = ""
                for currency, data in shift_summary['currencies'].items():
                    currency_text += f"• {currency}: ${data['amount']:,.2f} ({data['count']} ប្រតិបត្តិការ)\n"

                message = f"""
📊 របាយការណ៍វេនបច្ចុប្បន្ន #{current_shift.number}

🟢 ស្ថានភាព: សកម្ម
⏰ ចាប់ផ្តើម: {current_shift.start_time.strftime('%Y-%m-%d %H:%M')}
⏱️ រយៈពេល: {hours}ម៉ោង {minutes}នាទី

💰 សង្ខេបចំណូលសរុប:
{currency_text if currency_text else '• មិនទាន់មានប្រតិបត្តិការទេ'}
                """

                buttons = [
                    [("🛑 បិទបញ្ជី", "close_shift")],
                    [("🔙 ត្រឡប់ទៅមីនុយ", "back_to_menu")]
                ]

        except Exception as e:
            logger.error(f"Error showing current shift report: {e}")
            message = "❌ មានបញ្ហាក្នុងការទាញយករបាយការណ៍។ សូមសាកល្បងម្តងទៀត។"
            buttons = [[("🔙 ត្រឡប់ទៅមីនុយ", "back_to_menu")]]

        await event.edit(message, buttons=buttons)

    async def show_previous_shift_report(self, event):
        """Show previous shift report (last closed shift)"""
        chat_id = int(event.chat_id)

        try:
            previous_shifts = await self.shift_service.get_recent_closed_shifts(chat_id, 1)

            if not previous_shifts:
                message = """
📈 របាយការណ៍វេនមុន

🔴 គ្មានវេនដែលបានបិទ។

💡 វេនមុននឹងបង្ហាញនៅទីនេះបន្ទាប់ពីអ្នកបិទវេន។
                """
                buttons = [[("🔙 ត្រឡប់ទៅមីនុយ", "back_to_menu")]]
            else:
                shift = previous_shifts[0]
                shift_summary = await self.shift_service.get_shift_income_summary(shift.id)

                # Calculate duration
                duration = shift.end_time - shift.start_time
                total_seconds = abs(duration.total_seconds())
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)

                # Currency breakdown
                currency_text = ""
                for currency, data in shift_summary['currencies'].items():
                    currency_text += f"• {currency}: ${data['amount']:,.2f} ({data['count']} ប្រតិបត្តិការ)\n"

                message = f"""
📈 របាយការណ៍វេនមុន #{shift.number}

🔴 ស្ថានភាព: បានបិទ
⏰ ចាប់ផ្តើម: {shift.start_time.strftime('%Y-%m-%d %H:%M')}
⏱️ បញ្ចប់: {shift.end_time.strftime('%Y-%m-%d %H:%M')}
⏲️ រយៈពេល: {hours}ម៉ោង {minutes}នាទី

💰 ចំណូលសរុប:
{currency_text if currency_text else '• មិនទាន់មានប្រតិបត្តិការទេ'}
                """

                buttons = [[("🔙 ត្រឡប់ទៅមីនុយ", "back_to_menu")]]

        except Exception as e:
            logger.error(f"Error showing previous shift report: {e}")
            message = "❌ មានបញ្ហាក្នុងការទាញយករបាយការណ៍។ សូមសាកល្បងម្តងទៀត។"
            buttons = [[("🔙 ត្រឡប់ទៅមីនុយ", "back_to_menu")]]

        await event.edit(message, buttons=buttons)

    async def show_other_days_report(self, event):
        """Show other days with shifts (last 3 days with data)"""
        chat_id = int(event.chat_id)

        try:
            recent_dates = await self.shift_service.get_recent_dates_with_shifts(chat_id, 3)

            if not recent_dates:
                message = """
📅 របាយការណ៍ថ្ងៃផ្សេង

🔴 គ្មានទិន្នន័យសម្រាប់ថ្ងៃមុនៗ។

💡 ទិន្នន័យនឹងបង្ហាញនៅទីនេះបន្ទាប់ពីមានវេនបានបិទ។
                """
                buttons = [[("🔙 ត្រឡប់ទៅមីនុយ", "back_to_menu")]]
            else:
                message = "📅 របាយការណ៍ថ្ងៃផ្សេង\n\nជ្រើសរើសថ្ងៃដែលអ្នកចង់មើល:"

                buttons = []
                for date in recent_dates:
                    date_str = date.strftime("%Y-%m-%d")
                    display_date = date.strftime("%d %b %Y")
                    buttons.append([(display_date, f"date_{date_str}")])

                buttons.append([("🔙 ត្រឡប់ទៅមីនុយ", "back_to_menu")])

        except Exception as e:
            logger.error(f"Error showing other days report: {e}")
            message = "❌ មានបញ្ហាក្នុងការទាញយករបាយការណ៍។ សូមសាកល្បងម្តងទៀត។"
            buttons = [[("🔙 ត្រឡប់ទៅមីនុយ", "back_to_menu")]]

        await event.edit(message, buttons=buttons)

    async def show_date_shifts(self, event, data):
        """Show shifts for a specific date"""
        chat_id = int(event.chat_id)
        date_str = data.replace("date_", "")

        try:
            from datetime import datetime
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            shifts = await self.shift_service.get_shifts_by_date(chat_id, selected_date)

            if not shifts:
                message = f"""
📅 វេនសម្រាប់ថ្ងៃ {selected_date.strftime('%d %b %Y')}

🔴 គ្មានវេនសម្រាប់ថ្ងៃនេះ។
                """
                buttons = [
                    [("🔙 ត្រឡប់ទៅថ្ងៃផ្សេង", "other_days_report")],
                    [("🏠 ត្រឡប់ទៅមីនុយ", "back_to_menu")]
                ]
            else:
                message = f"📅 វេនសម្រាប់ថ្ងៃ {selected_date.strftime('%d %b %Y')}\n\nជ្រើសរើសវេនដែលអ្នកចង់មើល:"

                buttons = []
                for shift in shifts:
                    shift_summary = await self.shift_service.get_shift_income_summary(shift.id)
                    start_time = shift.start_time.strftime('%H:%M')
                    end_time = shift.end_time.strftime('%H:%M') if shift.end_time else "សកម្ម"
                    status = "🔴" if shift.is_closed else "🟢"

                    button_text = f"{status} វេន #{shift.number} ({start_time}-{end_time}) ${shift_summary['total_amount']:,.0f}"
                    buttons.append([(button_text, f"shift_{shift.id}")])

                buttons.extend([
                    [("🔙 ត្រឡប់ទៅថ្ងៃផ្សេង", "other_days_report")],
                    [("🏠 ត្រឡប់ទៅមីនុយ", "back_to_menu")]
                ])

        except Exception as e:
            logger.error(f"Error showing date shifts: {e}")
            message = "❌ មានបញ្ហាក្នុងការទាញយករបាយការណ៍។ សូមសាកល្បងម្តងទៀត។"
            buttons = [[("🔙 ត្រឡប់ទៅមីនុយ", "back_to_menu")]]

        await event.edit(message, buttons=buttons)

    async def show_specific_shift_report(self, event, data):
        """Show report for a specific shift"""
        shift_id = int(data.replace("shift_", ""))

        try:
            shift = await self.shift_service.get_shift_by_id(shift_id)

            if not shift:
                message = "❌ រកមិនឃើញវេននេះទេ។"
                buttons = [[("🔙 ត្រឡប់ទៅមីនុយ", "back_to_menu")]]
            else:
                shift_summary = await self.shift_service.get_shift_income_summary(shift.id)

                # Calculate duration
                if shift.end_time:
                    duration = shift.end_time - shift.start_time
                    end_text = shift.end_time.strftime('%Y-%m-%d %H:%M')
                    status = "🔴 បានបិទ"
                else:
                    from helper import DateUtils
                    duration = DateUtils.now() - shift.start_time
                    end_text = "បច្ចុប្បន្ន (វេនកំពុងសកម្ម)"
                    status = "🟢 សកម្ម"

                total_seconds = abs(duration.total_seconds())
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)

                # Currency breakdown
                currency_text = ""
                for currency, data in shift_summary['currencies'].items():
                    currency_text += f"• {currency}: ${data['amount']:,.2f} ({data['count']} ប្រតិបត្តិការ)\n"

                message = f"""
📊 របាយការណ៍វេន #{shift.number}

{status}
⏰ ចាប់ផ្តើម: {shift.start_time.strftime('%Y-%m-%d %H:%M')}
⏱️ បញ្ចប់: {end_text}
⏲️ រយៈពេល: {hours}ម៉ោង {minutes}នាទី

💰 សង្ខេបចំណូលសរុប:
{currency_text if currency_text else '• មិនទាន់មានប្រតិបត្តិការទេ'}
                """

                buttons = [
                    [("🔙 ត្រឡប់ទៅថ្ងៃផ្សេង", "other_days_report")],
                    [("🏠 ត្រឡប់ទៅមីនុយ", "back_to_menu")]
                ]

        except Exception as e:
            logger.error(f"Error showing specific shift report: {e}")
            message = "❌ មានបញ្ហាក្នុងការទាញយករបាយការណ៍។ សូមសាកល្បងម្តងទៀត។"
            buttons = [[("🔙 ត្រឡប់ទៅមីនុយ", "back_to_menu")]]

        await event.edit(message, buttons=buttons)

    async def close_current_shift(self, event):
        """Close the current active shift or create new shift if none exists"""
        chat_id = int(event.chat_id)
        logger.info(f"close_current_shift called for chat_id: {chat_id}")

        try:
            current_shift = await self.shift_service.get_current_shift(chat_id)

            if not current_shift:
                # No active shift, just create a new one
                new_shift = await self.shift_service.create_shift(chat_id)

                message = f"""
✅ វេនថ្មីត្រូវបានបង្កើតដោយជោគជ័យ!

📊 វេន #{new_shift.number}
⏰ ចាប់ផ្តើម: {new_shift.start_time.strftime('%Y-%m-%d %H:%M')}
🟢 ស្ថានភាព: សកម្ម

💡 ឥឡូវនេះប្រតិបត្តិការថ្មីទាំងអស់នឹងត្រូវបានកត់ត្រាក្នុងវេននេះ។
                """

                buttons = [[("🔙 ត្រឡប់ទៅមីនុយ", "back_to_menu")]]
            else:
                # Close the current shift and create new one
                closed_shift = await self.shift_service.close_shift(current_shift.id)

                if closed_shift:
                    # Automatically create a new shift after closing the current one
                    new_shift = await self.shift_service.create_shift(chat_id)

                    # Get final summary
                    shift_summary = await self.shift_service.get_shift_income_summary(closed_shift.id)
                    duration = closed_shift.end_time - closed_shift.start_time
                    total_seconds = abs(duration.total_seconds())
                    hours = int(total_seconds // 3600)
                    minutes = int((total_seconds % 3600) // 60)

                    message = f"""
✅ វេនត្រូវបានបិទដោយជោគជ័យ!

📊 សង្ខេបវេន #{closed_shift.number}:
⏰ ចាប់ផ្តើម: {closed_shift.start_time.strftime('%Y-%m-%d %H:%M')}
⏱️ បញ្ចប់: {closed_shift.end_time.strftime('%Y-%m-%d %H:%M')}
⏲️ រយៈពេល: {hours}ម៉ោង {minutes}នាទី

💰 លទ្ធផលចុងក្រោយ:
• សរុបចំណូល: ${shift_summary['total_amount']:,.2f}
• ប្រតិបត្តិការ: {shift_summary['transaction_count']}

🎉 ការងារល្អ!

🟢 វេនថ្មី #{new_shift.number} ត្រូវបានបង្កើតដោយស្វ័យប្រវត្តិ
                    """

                    buttons = [
                        [("📈 មើលវេនទាំងអស់", "other_days_report")],
                        [("🏠 ត្រឡប់ទៅមីនុយ", "back_to_menu")]
                    ]
                else:
                    message = "❌ បរាជ័យក្នុងការបិទវេន។ សូមសាកល្បងម្តងទៀត។"
                    buttons = [[("🔙 ត្រឡប់ទៅមីនុយ", "back_to_menu")]]

        except Exception as e:
            logger.error(f"Error closing shift: {e}")
            message = "❌ មានបញ្ហាក្នុងការបិទវេន។ សូមសាកល្បងម្តងទៀត។"
            buttons = [[("🔙 ត្រឡប់ទៅមីនុយ", "back_to_menu")]]

        await event.edit(message, buttons=buttons)

    async def close_menu(self, event):
        """Close the menu (delete message)"""
        try:
            await event.query.delete_message()
        except Exception as e:
            logger.error(f"Error deleting message: {e}")
            # Fallback to editing the message
            await event.edit("Menu closed.", buttons=None)

    async def show_support(self, event):
        """Show support information"""
        message = """
📞 ការគាំទ្រអាជីវកម្ម

🆘 ត្រូវការជំនួយ?
• បញ្ហាបច្ចេកទេសជាមួយបុត
• សំណួរអំពីលក្ខណៈពិសេសអាជីវកម្ម
• សំណើរបាយការណ៍ផ្ទាល់ខ្លួន
• ការគ្រប់គ្រងគណនី

📧 វិធីសាស្រ្តទំនាក់ទំនង:
• ការគាំទ្រក្នុងកម្មវិធី: ឆ្លើយតបសារនេះ
• អ៊ីមែល: business@yourcompany.com
• ទូរស័ព្ទ: +1-XXX-XXX-XXXX

⏰ ម៉ោងការគាំទ្រ:
ច័ន្ទ - សុក្រ: 9:00 AM - 6:00 PM
សៅរ៍: 10:00 AM - 2:00 PM
អាទិត្យ: បិទ

🚀 ការគាំទ្រពិសេស: មានសម្រាប់គណនីអាជីវកម្ម
        """

        buttons = [[("🔙 ត្រឡប់ទៅមីនុយ", "back_to_menu")]]
        await event.edit(message, buttons=buttons)