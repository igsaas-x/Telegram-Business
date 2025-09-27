from datetime import datetime

from helper.dateutils import DateUtils


def get_khmer_month_name(month_num: int) -> str:
    """Convert month number to Khmer month name"""
    khmer_months = {
        1: "មករា", 2: "កុម្ភៈ", 3: "មីនា", 4: "មេសា", 
        5: "ឧសភា", 6: "មិថុនា", 7: "កក្កដា", 8: "សីហា",
        9: "កញ្ញា", 10: "តុលា", 11: "វិច្ឆិកា", 12: "ធ្នូ"
    }
    return khmer_months.get(month_num, str(month_num))


def format_time_12hour(dt: datetime) -> str:
    """Format time in 12-hour format with AM/PM"""
    return dt.strftime("%I:%M%p").replace("AM", "AM").replace("PM", "PM")


async def daily_transaction_report(incomes, report_date: datetime, telegram_username: str = "Admin", group_name: str = None, chat_id: int = None) -> str:
    """Generate daily transaction report in the new format"""

    # Calculate totals and transaction counts
    totals = {"KHR": 0, "USD": 0}
    transaction_counts = {"KHR": 0, "USD": 0}

    transaction_times = []

    for income in incomes:
        currency = income.currency
        if currency in totals:
            totals[currency] += income.amount
            transaction_counts[currency] += 1
            transaction_times.append(income.income_date)

    # Get working hours from actual transaction times (first to last transaction)
    working_hours = ""
    if transaction_times:
        transaction_times.sort()
        start_time = format_time_12hour(transaction_times[0])
        end_time = format_time_12hour(transaction_times[-1])
        working_hours = f"{start_time} ➝ {end_time}"

    # Get current time for total hours display
    current_time = DateUtils.now()
    trigger_time = format_time_12hour(current_time)

    # Format date in Khmer
    day = report_date.day
    month_khmer = get_khmer_month_name(report_date.month)
    year = report_date.year

    # Build the report using HTML formatting
    report = "<b>សរុបប្រតិបត្តិការ</b>"
    report += f"<b>ថ្ងៃ {day} {month_khmer} {year}</b>\n"
    if group_name:
        report += f"<b>ក្រុម:</b> {group_name}\n"
    report += f"ម៉ោងបូកសរុប <b>{trigger_time}</b>\n"
    report += f"<i>(ដោយ: @{telegram_username})</i>\n"

    # KHR and USD amounts
    khr_amount = totals["KHR"]
    khr_count = transaction_counts["KHR"]
    khr_formatted = f"{khr_amount:,.0f}"

    usd_amount = totals["USD"]
    usd_count = transaction_counts["USD"]
    usd_formatted = f"{usd_amount:.2f}"

    # Use HTML table for better alignment
    report += "<pre>\n"
    report += f"(៛): {khr_formatted:<10} | ប្រតិបត្តិការ: {khr_count}\n"
    report += f"($): {usd_formatted:<10} | ប្រតិបត្តិការ: {usd_count}\n"
    report += "</pre>"


    if working_hours:
        report += f"<b>ម៉ោងប្រតិបត្តិការ:</b> <code>{working_hours}</code>"
    else:
        report += "<b>ម៉ោងប្រតិបត្តិការ:</b> គ្មាន"

    # Check if daily summary on shift close feature is enabled and add summary section
    if chat_id:
        from services import GroupPackageService
        from common.enums import FeatureFlags

        group_package_service = GroupPackageService()
        daily_summary_enabled = await group_package_service.has_feature(
            chat_id, FeatureFlags.DAILY_SUMMARY_ON_SHIFT_CLOSE.value
        )

        if daily_summary_enabled:
            # Add the same summary section as used in shift close and private bot
            summary = await daily_summary_for_shift_close(chat_id, report_date, group_name)
            report += summary

    return report


async def daily_summary_for_shift_close(chat_id: int, close_date: datetime, group_name: str = None) -> str:
    """Generate daily summary for shift close - shows all transactions for the day when feature is enabled"""
    from services import IncomeService
    from datetime import timedelta

    income_service = IncomeService()

    # Get all transactions for the entire day (not just the shift)
    start_of_day = close_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    incomes = await income_service.get_income_by_date_and_chat_id(
        chat_id=chat_id,
        start_date=start_of_day,
        end_date=end_of_day
    )

    if not incomes:
        return "\n\n📊 <b>សរុបថ្ងៃនេះ:</b> គ្មានប្រតិបត្តិការ"

    # Calculate totals for the entire day
    totals = {"KHR": 0, "USD": 0}
    transaction_counts = {"KHR": 0, "USD": 0}

    for income in incomes:
        currency = income.currency
        if currency in totals:
            totals[currency] += income.amount
            transaction_counts[currency] += 1

    # Format the daily summary section
    summary = "\n\n" + "——----- summary ———----" + "\n"
    summary += f"📊 <b>សរុបថ្ងៃ {close_date.strftime('%d-%m-%Y')}:</b>\n"

    # Format totals with same alignment as shift reports
    khr_formatted = f"{totals['KHR']:,.0f}"
    usd_formatted = f"{totals['USD']:.2f}"

    # Calculate spacing for alignment
    max_amount_length = max(len(khr_formatted), len(usd_formatted))
    khr_spaces_needed = max_amount_length - len(khr_formatted) + 4
    usd_spaces_needed = max_amount_length - len(usd_formatted) + 4

    # Wrap totals in pre tags for proper alignment
    total_data = f"KHR: {khr_formatted}{' ' * khr_spaces_needed}| ប្រតិបត្តិការ: {transaction_counts['KHR']}\n"
    total_data += f"USD: {usd_formatted}{' ' * usd_spaces_needed}| ប្រតិបត្តិការ: {transaction_counts['USD']}"

    summary += f"<pre>{total_data}</pre>"

    return summary