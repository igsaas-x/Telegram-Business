import logging

from models import ChatService, IncomeService, UserService
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

    async def menu(self, event):
        """Business-specific menu handler"""
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

        # Create menu buttons
        buttons = [
            [("📊 របាយការណ៍", "reports")],
            [("📞 ជំនួយ", "support")]
        ]

        message = """
🏢 ផ្ទាំងគ្រប់គ្រងអាជីវកម្ម

💼 ប្រព័ន្ធគ្រប់គ្រងហិរញ្ញវត្ថុអាជីវកម្ម
📊 តាមដានចំណូលនិងការវិភាគ

🔧 សកម្មភាពរហ័ស:
ជ្រើសរើសជម្រើសខាងក្រោមដើម្បីគ្រប់គ្រងអាជីវកម្មរបស់អ្នក។
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
        
        if data == "reports":
            await self.show_reports(event)
        elif data == "back_to_menu":
            await self.menu(event)
        elif data == "support":
            await self.show_support(event)
        else:
            # Fallback to regular command handler
            await self.command_handler.handle_callback_query(event)

    async def show_reports(self, event):
        """Show business reports"""
        message = """
📊 របាយការណ៍អាជីវកម្ម

📈 ការវិភាគដែលមាន:
• របាយការណ៍ប្រចាំថ្ងៃ
• របាយការណ៍ប្រចាំសប្តាហ៍ 
• របាយការណ៍ប្រចាំខែ
• ការវិភាគនិន្នាការ

💡 ប្រើម៉ឺនុយធម្មតាដើម្បីចូលប្រើរបាយការណ៍លម្អិត។
        """
        
        buttons = [[("🔙 ត្រឡប់ទៅមីនុយ", "back_to_menu")]]
        await event.edit(message, buttons=buttons)

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