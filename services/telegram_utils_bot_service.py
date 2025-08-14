import io

import qrcode
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

# Conversation state codes for Utils bot
START_MENU_CODE = 3000
WIFI_NAME_CODE = 3001
WIFI_PASSWORD_CODE = 3002


class TelegramUtilsBot:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.app: Application | None = None
        
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
            f"📶 WiFi Name: {wifi_name}\n\n"
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
            # Generate Utils code
            wifi_config = f"WIFI:T:WPA;S:{wifi_name};P:{wifi_password};;"
            
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(wifi_config)
            qr.make(fit=True)
            
            # Create QR code image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to bytes
            bio = io.BytesIO()
            img.save(bio, format='PNG')
            bio.seek(0)
            
            # Send the QR code image
            await update.message.reply_photo(
                photo=bio,
                caption=f"📶 Utils Code Generated!\n\n"
                       f"🏷️ Network: {wifi_name}\n"
                       f"🔐 Password: {'*' * len(wifi_password)}\n\n"
                       f"📱 Scan this QR code with your device to connect to the WiFi network!\n\n"
                       f"Use /start to generate another QR code."
            )
            
            force_log(f"Utils code generated for network: {wifi_name}", "TelegramUtilsBot")
            
            # Clear user data
            context.user_data.clear()
            
        except Exception as e:
            force_log(f"Error generating Utils code: {e}", "TelegramUtilsBot")
            await update.message.reply_text(
                "❌ Error generating QR code. Please try again with /start"
            )
        
        return ConversationHandler.END

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