from datetime import datetime


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


def daily_transaction_report(incomes, report_date: datetime, telegram_username: str = "Admin", start_date: datetime = None, end_date: datetime = None) -> str:
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
    current_time = datetime.now()
    trigger_time = format_time_12hour(current_time)
    
    # Format date in Khmer
    day = report_date.day
    month_khmer = get_khmer_month_name(report_date.month)
    year = report_date.year
    
    # Build the report
    report = "សរុបប្រតិបត្តិការ\n"
    report += f"ថ្ងៃ {day} {month_khmer} {year} — ម៉ោងបូកសរុប {trigger_time} \n(ដោយ: {telegram_username})\n"
    report += "- - - - - - - - - - - - - - - - - - - - - \n"
    
    # KHR line
    khr_amount = totals["KHR"]
    khr_count = transaction_counts["KHR"]
    khr_formatted = f"{khr_amount:,.0f}"
    
    # USD line  
    usd_amount = totals["USD"]
    usd_count = transaction_counts["USD"]
    usd_formatted = f"{usd_amount:.2f}"
    
    # Calculate spacing to align the pipes regardless of amount length
    max_amount_length = max(len(khr_formatted), len(usd_formatted))
    
    # Calculate exact spacing needed to align pipes
    khr_spaces_needed = max_amount_length - len(khr_formatted) + 4  # 4 base spaces
    usd_spaces_needed = max_amount_length - len(usd_formatted) + 5
    
    report += f"(៛): {khr_formatted}{' ' * khr_spaces_needed}| ប្រតិបត្តិការ: {khr_count}\n"
    report += f"($): {usd_formatted}{' ' * usd_spaces_needed}| ប្រតិបត្តិការ: {usd_count}\n"
    
    report += "- - - - - - - - - - - - - - - - - - - - - \n"
    
    if working_hours:
        report += f"ម៉ោងប្រតិបត្តិការ: {working_hours}"
    else:
        report += "ម៉ោងប្រតិបត្តិការ: គ្មាន"
    
    return report