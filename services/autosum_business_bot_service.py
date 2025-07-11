import logging

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    Application,
    ConversationHandler,
    CallbackQueryHandler,
)

from handlers.business_event_handler import BusinessEventHandler
from models import ChatService, UserService

# Get logger
logger = logging.getLogger(__name__)

# Business bot specific conversation states
BUSINESS_MENU_CODE = 2001
BUSINESS_SUMMARY_CODE = 2002
BUSINESS_ANALYTICS_CODE = 2003
BUSINESS_SETTINGS_CODE = 2004
BUSINESS_CALLBACK_CODE = 2005


class AutosumBusinessBot:
    """
    Specialized business bot with different event handling and features
    """
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.app: Application | None = None
        self.chat_service = ChatService()
        self.user_service = UserService()
        self.event_handler = BusinessEventHandler()
        logger.info("AutosumBusinessBot initialized with token")

    async def business_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Business bot start command with specialized welcome message"""
        welcome_message = """
🏢 **Welcome to Autosum Business!**

💼 **Your Business Finance Assistant**

This bot provides advanced business features:
• 📊 Real-time revenue tracking
• 📈 Business analytics and insights
• 🔄 Shift management for teams
• 💰 Multi-currency support
• 📱 Mobile-friendly dashboard

🚀 **Getting Started:**
1. Use /menu to access the business dashboard
2. Register your chat for business services
3. Start tracking your revenue automatically

💡 **Pro Tip:** Enable shift tracking for detailed performance analysis.

Type /menu to begin managing your business finances!
        """
        
        await update.message.reply_text(welcome_message)

    async def business_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Business-specific menu handler"""
        # Create a mock event object for the business event handler
        class MockEvent:
            def __init__(self, update):
                self.chat_id = update.effective_chat.id
                self.chat = update.effective_chat
                
            async def respond(self, message, buttons=None):
                if buttons:
                    # Convert tuples to InlineKeyboardButton objects
                    keyboard_buttons = []
                    for row in buttons:
                        button_row = []
                        for button in row:
                            if isinstance(button, tuple) and len(button) == 2:
                                text, callback_data = button
                                button_row.append(InlineKeyboardButton(text, callback_data=callback_data))
                        keyboard_buttons.append(button_row)
                    
                    await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard_buttons))
                else:
                    await update.message.reply_text(message)
                    
            async def get_sender(self):
                return update.effective_user

        mock_event = MockEvent(update)
        
        try:
            await self.event_handler.menu(mock_event)
            return BUSINESS_MENU_CODE
        except Exception as e:
            logger.error(f"Error in business menu: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            await update.message.reply_text("❌ Error loading business menu. Please try again.")
            return ConversationHandler.END

    async def handle_business_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle business-specific callback queries"""
        query = update.callback_query
        await query.answer()
        
        # Create a mock event for the business handler
        class MockCallbackEvent:
            def __init__(self, query):
                self.chat_id = query.message.chat_id
                self.data = query.data.encode('utf-8')
                self.query = query
                
            async def edit(self, message, buttons=None):
                if buttons:
                    # Convert tuples to InlineKeyboardButton objects
                    keyboard_buttons = []
                    for row in buttons:
                        button_row = []
                        for button in row:
                            if isinstance(button, tuple) and len(button) == 2:
                                text, callback_data = button
                                button_row.append(InlineKeyboardButton(text, callback_data=callback_data))
                        keyboard_buttons.append(button_row)
                    
                    await self.query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard_buttons))
                else:
                    await self.query.edit_message_text(message)

        mock_event = MockCallbackEvent(query)
        
        try:
            if query.data == "back_to_menu":
                # Return to main business menu
                await self.business_menu(update, context)
                return BUSINESS_MENU_CODE
            else:
                await self.event_handler.handle_business_callback(mock_event)
                return BUSINESS_CALLBACK_CODE
        except Exception as e:
            logger.error(f"Error handling business callback: {e}")
            await query.edit_message_text("❌ Error processing request. Please try again.")
            return ConversationHandler.END

    async def business_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Business bot help command"""
        help_message = """
🏢 **Autosum Business Bot Help**

📋 **Available Commands:**
• `/start` - Welcome message and introduction
• `/menu` - Access business dashboard
• `/help` - Show this help message
• `/support` - Contact business support

💼 **Business Features:**
• **Revenue Tracking** - Automatic transaction monitoring
• **Analytics** - Business insights and trends
• **Shift Management** - Track performance by work shifts
• **Multi-Currency** - Support for different currencies
• **Reports** - Daily, weekly, and monthly summaries

🔧 **Dashboard Options:**
• 📊 Business Summary - Overview of your performance
• 💰 Daily Revenue - Today's transaction details
• 📈 Analytics - Advanced business insights
• 🔄 Shift Management - Organize by work periods
• ⚙️ Settings - Configure bot preferences

📞 **Need Help?**
Use /support for technical assistance or business inquiries.

💡 **Pro Tips:**
• Register your chat to start tracking automatically
• Enable shift mode for detailed team performance
• Check daily revenue for real-time insights
        """
        
        await update.message.reply_text(help_message)

    async def business_support(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Business support command"""
        support_message = """
📞 **Business Support Center**

🆘 **Quick Help:**
• Bot not responding? Try /start to refresh
• Missing transactions? Check chat registration
• Need custom features? Contact our team

📧 **Contact Information:**
• **Email:** business@autosum.com
• **Phone:** +1-XXX-XXX-XXXX
• **Support Hours:** Mon-Fri 9AM-6PM EST

🚀 **Business Services:**
• Custom reporting solutions
• API integrations
• Team training sessions
• Premium analytics features

💬 **Instant Support:**
Reply to this message with your question, and our team will respond within 24 hours.

🔗 **Resources:**
• User Guide: /help
• Dashboard: /menu
• Feature Requests: Contact support team
        """
        
        await update.message.reply_text(support_message)

    def setup(self):
        """Setup the business bot with specialized handlers"""
        if not self.bot_token:
            raise ValueError("Business bot token is required")
            
        self.app = ApplicationBuilder().token(self.bot_token).build()

        # Business-specific command handlers
        self.app.add_handler(CommandHandler("start", self.business_start))
        self.app.add_handler(CommandHandler("help", self.business_help))
        self.app.add_handler(CommandHandler("support", self.business_support))

        # Business menu conversation handler
        business_menu_handler = ConversationHandler(
            entry_points=[CommandHandler("menu", self.business_menu)],
            states={
                BUSINESS_MENU_CODE: [
                    CallbackQueryHandler(self.handle_business_callback),
                ],
                BUSINESS_CALLBACK_CODE: [
                    CallbackQueryHandler(self.handle_business_callback),
                ],
            },
            fallbacks=[CommandHandler("menu", self.business_menu)],
            per_message=False,
        )

        self.app.add_handler(business_menu_handler)

        # Add error handler
        self.app.add_error_handler(self.error_handler)

        logger.info("AutosumBusinessBot setup completed")

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors in the business bot"""
        logger.error(f"Business bot error: {context.error}")
        
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An error occurred in the business bot. Please try again or contact support."
            )

    async def start_polling(self):
        """Start the business bot polling"""
        try:
            self.setup()
            logger.info("Starting AutosumBusinessBot polling...")
            
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling()
            
            logger.info("AutosumBusinessBot is running and polling for updates...")
            
            # Keep the bot running indefinitely
            try:
                await self.app.updater.idle()
            except Exception:
                # If idle fails, just wait indefinitely
                import asyncio
                while True:
                    await asyncio.sleep(3600)  # Sleep for 1 hour at a time
            
        except Exception as e:
            logger.error(f"Error starting AutosumBusinessBot: {e}")
            raise

    async def stop(self):
        """Stop the business bot"""
        if self.app:
            try:
                await self.app.updater.stop()
                await self.app.stop()
                await self.app.shutdown()
                logger.info("AutosumBusinessBot stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping AutosumBusinessBot: {e}")