from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_menu_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("ថ្ងៃ", callback_data='daily_summary'),
        InlineKeyboardButton("សប្ដាហ៍", callback_data='weekly_summary'),
        InlineKeyboardButton("ខែ", callback_data='monthly_summary')
    ]])

async def handle_main_menu(self, update, context):
    query = update.callback_query
    keyboard = [
        [
            InlineKeyboardButton("ថ្ងៃ", callback_data='daily_summary'),
            InlineKeyboardButton("សប្ដាហ៍", callback_data='weekly_summary'),
            InlineKeyboardButton("ខែ", callback_data='monthly_summary')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="ជ្រើសរើសរបាយការណ៍ប្រចាំ:",
        reply_markup=reply_markup
    )