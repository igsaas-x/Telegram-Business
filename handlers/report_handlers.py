from telethon import Button
from datetime import datetime, timedelta
from models.income_balance import IncomeService, CurrencyEnum
from calendar import monthrange
# No longer using get_main_menu_keyboard

user_date_input_state = {}

class ReportHandler:
    @staticmethod
    def generate_summary_buttons(periods, label_func, callback_prefix):
        buttons = []
        for period in periods:
            label = label_func(period)
            callback_data = f"{callback_prefix}{period['callback_value']}"
            buttons.append([Button.inline(label, callback_data)])
        return buttons

    @staticmethod
    def get_back_button(period_type: str = "daily"):
        callback_data = {
            "week": "weekly_summary",
            "month": "monthly_summary",
            "daily": "daily_summary"
        }.get(period_type, "daily_summary")
        return [[Button.inline("ត្រឡប់ក្រោយ", callback_data)]]

    @staticmethod
    def format_totals_message(period_text: str, incomes):
        totals = {currency.name: 0 for currency in CurrencyEnum}
        for income in incomes:
            if income.currency in totals:
                totals[income.currency] += income.amount
            else:
                totals[income.currency] = income.amount

        message = f"សរុបប្រតិបត្តិការ {period_text}:\n\n"
        for currency in CurrencyEnum:
            code = currency.name
            symbol = currency.value
            total = totals.get(code, 0)
            message += f"{symbol} ({code}): {total:,.2f}\n"
        return message

    async def handle_date_summary(self, update, context):
        """Handle specific date summary request."""
        query = update.callback_query
        chat_id = update.effective_chat.id
        date_str = query.data.replace("summary_of_", "")
        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d")
            income_service = IncomeService()
            incomes = await income_service.get_income_by_date_and_chat_id(
                chat_id=chat_id,
                start_date=selected_date,
                end_date=selected_date + timedelta(days=1)
            )
            if not incomes:
                await query.edit_message_text(
                    text=f"គ្មានប្រតិបត្តិការសម្រាប់ថ្ងៃទី {selected_date.strftime('%d %b %Y')} ទេ។",
                    reply_markup=self.get_back_button()
                )
                return
            message = self.format_totals_message(
                f"ថ្ងៃទី {selected_date.strftime('%d %b %Y')}", incomes
            )
            await query.edit_message_text(
                text=message,
                reply_markup=self.get_back_button()
            )
        except ValueError:
            await query.edit_message_text(
                text="ទម្រង់កាលបរិច្ឆេទមិនត្រឹមត្រូវ",
                reply_markup=self.get_back_button()
            )

    async def handle_daily_summary(self, update, context):
        query = update.callback_query
        today = datetime.now()
        periods = []
        for i in range(2, -1, -1):
            day = today - timedelta(days=i)
            periods.append({
                "label": day.strftime("%b %d"),
                "callback_value": day.strftime("%Y-%m-%d")
            })
        buttons = self.generate_summary_buttons(
            periods,
            label_func=lambda p: p["label"],
            callback_prefix="summary_of_"
        )
        buttons.append([InlineKeyboardButton("ថ្ងៃផ្សេងទៀត", callback_data="other_dates")])
        buttons.append([InlineKeyboardButton("ត្រឡប់ក្រោយ", callback_data="menu")])
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(
            text="ឆែករបាយការណ៍ថ្ងៃ:",
            reply_markup=reply_markup
        )

    async def handle_weekly_summary(self, update, context):
        query = update.callback_query
        now = datetime.now()
        year = now.year
        month = now.month
        last_day = monthrange(year, month)[1]

        week_ranges = [
            (1, 7),
            (8, 14),
            (15, 21),
            (22, last_day)
        ]

        periods = []
        for start_day, end_day in week_ranges:
            start_date = datetime(year, month, start_day)
            end_date = datetime(year, month, min(end_day, last_day))
            periods.append({
                "label": f"{start_date.strftime('%d %b')} - {end_date.strftime('%d %b')}",
                "callback_value": start_date.strftime("%Y-%m-%d")
            })

        buttons = self.generate_summary_buttons(
            periods,
            label_func=lambda p: p["label"],
            callback_prefix="summary_week_"
        )
        buttons.append([InlineKeyboardButton("ត្រឡប់ក្រោយ", callback_data="menu")])
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(
            text="ជ្រើសរើសសប្តាហ៍:",
            reply_markup=reply_markup
        )

    async def handle_monthly_summary(self, update, context):
        query = update.callback_query
        now = datetime.now()
        year = now.year
        periods = []
        for month in range(1, 13):
            month_date = datetime(year, month, 1)
            periods.append({
                "label": month_date.strftime("%B %Y"),
                "callback_value": month_date.strftime("%Y-%m")
            })
        buttons = self.generate_summary_buttons(
            periods,
            label_func=lambda p: p["label"],
            callback_prefix="summary_month_"
        )
        buttons.append([InlineKeyboardButton("ត្រឡប់ក្រោយ", callback_data="menu")])
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(
            text="ជ្រើសរើសខែ:",
            reply_markup=reply_markup
        )

    async def handle_period_summary(self, update, context):
        query = update.callback_query
        chat_id = update.effective_chat.id
        data = query.data
        try:
            if data.startswith("summary_week_"):
                start_date = datetime.strptime(data.replace("summary_week_", ""), "%Y-%m-%d")
                end_date = start_date + timedelta(days=7)
                period_text = f"{start_date.strftime('%d')} - {(end_date - timedelta(days=1)).strftime('%d %b %Y')}"
                back_type = "week"
            elif data.startswith("summary_month_"):
                start_date = datetime.strptime(data.replace("summary_month_", ""), "%Y-%m")
                _, last_day = monthrange(start_date.year, start_date.month)
                end_date = start_date.replace(day=last_day) + timedelta(days=1)
                period_text = start_date.strftime("%B %Y")
                back_type = "month"
            else:
                raise ValueError("Invalid period format")
            income_service = IncomeService()
            incomes = await income_service.get_income_by_date_and_chat_id(
                chat_id=chat_id,
                start_date=start_date,
                end_date=end_date
            )
            if not incomes:
                await query.edit_message_text(
                    text=f"គ្មានប្រតិបត្តិការសម្រាប់ {period_text} ទេ។",
                    reply_markup=self.get_back_button(back_type)
                )
                return
            message = self.format_totals_message(period_text, incomes)
            await query.edit_message_text(
                text=message,
                reply_markup=self.get_back_button(back_type)
            )
        except ValueError:
            await query.edit_message_text(
                text="ទម្រង់កាលបរិច្ឆេទមិនត្រឹមត្រូវ",
                reply_markup=self.get_back_button("daily")
            )

    async def handle_main_menu(self, update, context):
        query = update.callback_query
        reply_markup = get_main_menu_keyboard()
        await query.edit_message_text(
            text="ជ្រើសរើសរបាយការណ៍ប្រចាំ:",
            reply_markup=reply_markup
        )

    async def handle_other_dates(self, update, context):
        query = update.callback_query
        chat_id = update.effective_chat.id
        user_date_input_state[chat_id] = True  
        await query.edit_message_text(
            text="ឆែករបាយការណ៍ថ្ងៃទី:"
        )

async def handle_date_input(update, context):
    chat_id = update.effective_chat.id
    if user_date_input_state.get(chat_id):
        day_str = update.message.text.strip()
        now = datetime.now()
        year = now.year
        month = now.month
        try:
            day = int(day_str)
            last_day = monthrange(year, month)[1]
            if not (1 <= day <= last_day):
                raise ValueError("Invalid day")
            selected_date = datetime(year, month, day)
            income_service = IncomeService()
            incomes = await income_service.get_income_by_date_and_chat_id(
                chat_id=chat_id,
                start_date=selected_date,
                end_date=selected_date + timedelta(days=1)
            )
            if not incomes:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"គ្មានប្រតិបត្តិការសម្រាប់ថ្ងៃទី {selected_date.strftime('%d %b %Y')} ទេ។"
                )
            else:
                message = ReportHandler.format_totals_message(
                    f"ថ្ងៃទី {selected_date.strftime('%d %b %Y')}", incomes
                )
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message
                )
        except Exception:
            await context.bot.send_message(
                chat_id=chat_id,
                text="កាលបរិច្ឆេទដែលត្រឹមត្រូវទេ។"
            )
        user_date_input_state[chat_id] = False