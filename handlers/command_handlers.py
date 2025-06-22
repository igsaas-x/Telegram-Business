from telegram import  InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler
from helper.get_main_menu_keyword import get_main_menu_keyboard
from services.registration import RegistrationService

async def menu(update, context):
    reply_markup = get_main_menu_keyboard()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="ជ្រើសរើសរបាយការណ៍ប្រចាំ:",
        parse_mode='MarkdownV2',
        reply_markup=reply_markup
    )

async def register(update, context):
    chat_id = update.effective_chat.id
    service = RegistrationService()
    success = await service.register_chat(chat_id)
    if success:
        await context.bot.send_message(
            chat_id=chat_id,
            text="You have been registered successfully!"
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text="You are already registered."
        )

menu_handler = CommandHandler("menu", menu)
register_handler = CommandHandler("register", register)

