from telethon import Button

def get_main_menu_keyboard():
    return [
        [Button.inline("ថ្ងៃ", 'daily_summary'),
        Button.inline("សប្ដាហ៍", 'weekly_summary'),
        Button.inline("ខែ", 'monthly_summary')]
    ]

async def handle_main_menu(event):
    buttons = [
        [
            Button.inline("ថ្ងៃ", 'daily_summary'),
            Button.inline("សប្ដាហ៍", 'weekly_summary'),
            Button.inline("ខែ", 'monthly_summary')
        ]
    ]
    await event.edit("ជ្រើសរើសរបាយការណ៍ប្រចាំ:", buttons=buttons)