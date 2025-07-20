from datetime import datetime

from .daily_report_helper import get_khmer_month_name


def monthly_transaction_report(incomes, start_date: datetime, end_date: datetime) -> str:
    """Generate monthly transaction report in format similar to weekly report"""
    from datetime import date

    # Group transactions by date
    daily_data = {}
    transaction_times = []
    
    for income in incomes:
        income_date = income.income_date.date()
        if income_date not in daily_data:
            daily_data[income_date] = {"KHR": 0, "USD": 0, "count": 0}
        
        currency = income.currency
        daily_data[income_date][currency] += income.amount
        daily_data[income_date]["count"] += 1
        transaction_times.append(income.income_date)
    
    # Calculate totals
    total_khr = sum(day_data["KHR"] for day_data in daily_data.values())
    total_usd = sum(day_data["USD"] for day_data in daily_data.values())
    total_transactions = sum(day_data["count"] for day_data in daily_data.values())
    
    # Get working hours from actual transaction times (first to last transaction)
    # working_hours = ""
    # if transaction_times:
    #     transaction_times.sort()
    #     start_time = format_time_12hour(transaction_times[0])
    #     end_time = format_time_12hour(transaction_times[-1])
    #     working_hours = f"{start_time} ➝ {end_time}"
    
    # Format date range for title
    month_khmer = get_khmer_month_name(start_date.month)
    year = start_date.year
    
    # Build the report
    report = f"សរុបប្រតិបត្តិការ {month_khmer} {year}\n\n"
    
    # Determine the actual end date for the report
    # If the month hasn't ended yet, only show up to current date
    today = date.today()
    current_date = start_date.date()
    end_date_actual = end_date.date()
    
    # If we're in the same month as start_date and haven't reached end_date yet, 
    # limit to today's date
    if (today.year == start_date.year and 
        today.month == start_date.month and 
        today < end_date_actual):
        from datetime import timedelta
        end_date_actual = today + timedelta(days=1)  # Add 1 day to include today
    
    # Calculate column widths for proper alignment
    # First pass: collect all formatted amounts to determine max widths
    daily_rows = []
    
    while current_date < end_date_actual:
        day_num = current_date.day
        day_data = daily_data.get(current_date, {"KHR": 0, "USD": 0, "count": 0})
        
        khr_formatted = f"{day_data['KHR']:,.0f}"
        usd_formatted = f"{day_data['USD']:,.2f}"
        trans_count = day_data['count']
        
        daily_rows.append({
            'day': day_num,
            'khr': khr_formatted,
            'usd': usd_formatted,
            'count': trans_count
        })
        
        # Move to next day using timedelta (much simpler and more reliable)
        from datetime import timedelta
        current_date = current_date + timedelta(days=1)
    
    # Calculate maximum widths for alignment
    max_khr_width = max(len(row['khr']) for row in daily_rows) if daily_rows else 8
    max_usd_width = max(len(row['usd']) for row in daily_rows) if daily_rows else 6
    
    # Also consider the totals for width calculation
    total_khr_formatted = f"{total_khr:,.0f}"
    total_usd_formatted = f"{total_usd:,.2f}"
    max_khr_width = max(max_khr_width, len(total_khr_formatted))
    max_usd_width = max(max_usd_width, len(total_usd_formatted))
    
    # Create header with proper spacing
    report += f"ថ្ងៃ  {'(៛)':<{max_khr_width}}  {'($)':<{max_usd_width}}  សរុប(Trans.)\n"
    report += "- - - - - - - - - - - - - - - - - - - - - \n"
    
    # Generate daily rows with proper alignment
    for row in daily_rows:
        report += f"{row['day']:<2}  {row['khr']:<{max_khr_width+4}}  {row['usd']:<{max_usd_width+4}}  {row['count']}\n"
    
    report += "- - - - - - - - - - - - - - - - - - - - - \n"
    report += f"សរុប: {total_khr_formatted:<{max_khr_width}}  {total_usd_formatted:<{max_usd_width}}  {total_transactions}\n"
    
    # if working_hours:
    #     report += f"ម៉ោងប្រតិបត្តិការ: {working_hours}"
    # else:
    #     report += "ម៉ោងប្រតិបត្តិការ: គ្មាន"
    
    return report