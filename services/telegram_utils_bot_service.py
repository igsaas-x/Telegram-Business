from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    Application,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from helper.logger_utils import force_log
from helper.pdf_generator import PDFGenerator
from helper.qr_generator import QRGenerator

# Conversation state codes for Utils bot
START_MENU_CODE = 3000
WIFI_NAME_CODE = 3001
WIFI_PASSWORD_CODE = 3002
PDF_OPTION_CODE = 3003


class TelegramUtilsBot:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.app: Application | None = None
        self.qr_generator = QRGenerator()
        self.pdf_generator = PDFGenerator()
        
        force_log("TelegramUtilsBot initialized with token", "TelegramUtilsBot")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        keyboard = [
            [InlineKeyboardButton("📶 Generate Utils Code", callback_data="generate_wifi_qr")],
            [InlineKeyboardButton("❌ Cancel", callback_data="close_conversation")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔧 Welcome to Utils Code Generator!\n\n"
            "This bot helps you generate QR codes for WiFi networks.\n"
            "Choose an option:",
            reply_markup=reply_markup
        )
        return START_MENU_CODE

    async def handle_start_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle start menu button selections"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "generate_wifi_qr":
            await query.edit_message_text(
                "📶 Let's generate a Utils code!\n\n"
                "Please enter the WiFi network name (SSID):"
            )
            return WIFI_NAME_CODE
        elif query.data == "close_conversation":
            await query.edit_message_text("Goodbye! Use /start anytime to generate Utils codes.")
            return ConversationHandler.END
        
        return ConversationHandler.END

    async def handle_wifi_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle WiFi name input"""
        wifi_name = update.message.text.strip()
        
        if not wifi_name:
            await update.message.reply_text(
                "❌ WiFi name cannot be empty. Please enter a valid WiFi network name:"
            )
            return WIFI_NAME_CODE
        
        # Store the WiFi name in context
        context.user_data["wifi_name"] = wifi_name
        
        await update.message.reply_text(
            f"📶 Wifi Name: {wifi_name}\n\n"
            "🔐 Now please enter the WiFi password:"
        )
        
        return WIFI_PASSWORD_CODE

    async def handle_wifi_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle WiFi password input and generate QR code"""
        wifi_password = update.message.text.strip()
        wifi_name = context.user_data.get("wifi_name", "")
        
        if not wifi_password:
            await update.message.reply_text(
                "❌ WiFi password cannot be empty. Please enter the WiFi password:"
            )
            return WIFI_PASSWORD_CODE
        
        try:
            # Send "generating" message first
            generating_msg = await update.message.reply_text(
                "🔧 Generating WiFi QR code...\n"
                "⏳ Please wait..."
            )
            
            # Generate WiFi QR code with text using utility class
            final_img = self.qr_generator.generate_wifi_qr_with_text(wifi_name, wifi_password)
            
            # Convert to bytes for sending
            bio = self.qr_generator.image_to_bytes(final_img)
            
            # Store the QR image data for potential PDF generation
            context.user_data["qr_image"] = final_img
            context.user_data["wifi_name"] = wifi_name
            context.user_data["wifi_password"] = wifi_password
            
            # Create keyboard with PDF option
            keyboard = [
                [InlineKeyboardButton("📄 Generate as PDF", callback_data="generate_pdf")],
                [InlineKeyboardButton("✅ Done", callback_data="done")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Delete the generating message
            await generating_msg.delete()
            
            # Send the QR code image
            await update.message.reply_photo(
                photo=bio,
                caption=f"📶 WiFi QR Code Generated!\n\n"
                       f"🏷️ Network: {wifi_name}\n"
                       f"🔐 Password: {'*' * len(wifi_password)}\n\n"
                       f"📱 Scan this QR code with your device to connect to the WiFi network!\n\n"
                       f"Choose an option below:",
                reply_markup=reply_markup
            )
            
            force_log(f"Utils code generated for network: {wifi_name}", "TelegramUtilsBot")
            
            return PDF_OPTION_CODE
            
        except Exception as e:
            force_log(f"Error generating Utils code: {e}", "TelegramUtilsBot")
            await update.message.reply_text(
                "❌ Error generating QR code. Please try again with /start"
            )
        
        return ConversationHandler.END

    async def handle_pdf_option(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle PDF generation option"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "generate_pdf":
            await self.generate_pdf(query, context)
        elif query.data == "done":
            await query.edit_message_caption(
                caption=f"{query.message.caption}\n\n✅ Completed! Use /start to generate another QR code."
            )
            context.user_data.clear()
            return ConversationHandler.END
        
        return PDF_OPTION_CODE

    async def generate_pdf(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Generate and send PDF version of the QR code using utility class"""
        try:
            qr_image = context.user_data.get("qr_image")
            wifi_name = context.user_data.get("wifi_name", "")
            
            if not qr_image:
                await query.edit_message_caption(
                    caption=f"{query.message.caption}\n\n❌ Error: QR code data not found."
                )
                return
            
            # Generate PDF using utility class
            pdf_buffer = self.pdf_generator.create_wifi_qr_pdf(qr_image, wifi_name)
            filename = self.pdf_generator.get_pdf_filename(wifi_name)
            
            # Send PDF document
            await query.message.reply_document(
                document=pdf_buffer,
                filename=filename,
                caption=f"📄 PDF version ready for printing! 🖨️"
            )
            
            await query.edit_message_caption(
                caption=f"{query.message.caption}\n\n✅ PDF generated and sent! Use /start to generate another QR code."
            )
            
            force_log(f"PDF generated for WiFi network: {wifi_name}", "TelegramUtilsBot")
            context.user_data.clear()
            
        except Exception as e:
            force_log(f"Error generating PDF: {e}", "TelegramUtilsBot")
            await query.edit_message_caption(
                caption=f"{query.message.caption}\n\n❌ Error generating PDF. Please try again."
            )

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel command"""
        await update.message.reply_text("Operation cancelled. Use /start to begin again.")
        context.user_data.clear()
        return ConversationHandler.END

    def setup(self):
        """Set up the bot handlers"""
        self.app = ApplicationBuilder().token(self.bot_token).build()

        # Main conversation handler
        main_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start_command)],
            states={
                START_MENU_CODE: [CallbackQueryHandler(self.handle_start_menu)],
                WIFI_NAME_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_wifi_name)],
                WIFI_PASSWORD_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_wifi_password)],
                PDF_OPTION_CODE: [CallbackQueryHandler(self.handle_pdf_option)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_chat=True,
            per_user=True,
        )

        # Add handlers
        self.app.add_handler(main_handler)

        force_log("TelegramUtilsBot handlers set up", "TelegramUtilsBot")

    async def start_polling(self):
        """Start the bot polling"""
        if not self.app:
            self.setup()

        assert self.app is not None
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()  # type: ignore
        force_log("TelegramUtilsBot started polling", "TelegramUtilsBot")