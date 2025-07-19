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


def daily_transaction_report(incomes, report_date: datetime, telegram_username: str = "Admin") -> str:
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
    
    # Get working hours from first and last transactions
    working_hours = ""
    if transaction_times:
        transaction_times.sort()
        start_time = format_time_12hour(transaction_times[0])
        end_time = format_time_12hour(transaction_times[-1])
        working_hours = f"{start_time} ➝ {end_time}"
    
    # Get total working time (simplified calculation)
    total_hours = "0:00PM"
    if transaction_times and len(transaction_times) > 1:
        duration = transaction_times[-1] - transaction_times[0]
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        # Use end time format for total hours display
        total_hours = format_time_12hour(transaction_times[-1])
    elif transaction_times:
        total_hours = format_time_12hour(transaction_times[0])
    
    # Format date in Khmer
    day = report_date.day
    month_khmer = get_khmer_month_name(report_date.month)
    year = report_date.year
    
    # Build the report
    report = "សរុបប្រតិបត្តិការ\n"
    report += f"ថ្ងៃ {day} {month_khmer} {year} — ម៉ោងបូកសរុប {total_hours} (ដោយ: {telegram_username})\n"
    report += "- - - - - - - - - - - - - -- - - - - - - \n"
    
    # KHR line
    khr_amount = totals["KHR"]
    khr_count = transaction_counts["KHR"]
    khr_formatted = f"{khr_amount:,.0f}"
    
    # USD line  
    usd_amount = totals["USD"]
    usd_count = transaction_counts["USD"]
    usd_formatted = f"{usd_amount:.2f}"
    
    # Calculate spacing to align the pipes
    # Find the longer formatted amount and pad the shorter one
    max_amount_length = max(len(khr_formatted), len(usd_formatted))
    khr_padding = max_amount_length - len(khr_formatted)
    usd_padding = max_amount_length - len(usd_formatted)
    
    report += f"(៛): {khr_formatted}{' ' * khr_padding}        |  ប្រតិបត្តិការណ៍: {khr_count}\n"
    report += f"($): {usd_formatted}{' ' * usd_padding}        | ប្រតិបត្តិការណ៍: {usd_count}\n"
    
    report += "- - - - - - - - - - - - - -- - - - - - - \n"
    
    if working_hours:
        report += f"ម៉ោងប្រតិបត្តិការ: {working_hours}"
    else:
        report += "ម៉ោងប្រតិបត្តិការ: គ្មាន"
    
    return report