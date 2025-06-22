from telegram import  InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler
from helper.get_main_menu_keyword import get_main_menu_keyboard

async def menu(update, context):
    reply_markup = get_main_menu_keyboard()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="ជ្រើសរើសរបាយការណ៍ប្រចាំ:",
        parse_mode='MarkdownV2',
        reply_markup=reply_markup
    )


menu_handler = CommandHandler("menu", menu)


