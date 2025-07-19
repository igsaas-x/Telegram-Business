from datetime import datetime

from .daily_report_helper import get_khmer_month_name


def weekly_transaction_report(incomes, start_date: datetime, end_date: datetime) -> str:
    """Generate weekly transaction report in the specified format"""
    
    # Group transactions by date
    daily_data = {}
    
    for income in incomes:
        income_date = income.income_date.date()
        if income_date not in daily_data:
            daily_data[income_date] = {"KHR": 0, "USD": 0, "count": 0}
        
        currency = income.currency
        daily_data[income_date][currency] += income.amount
        daily_data[income_date]["count"] += 1
    
    # Calculate totals
    total_khr = sum(day_data["KHR"] for day_data in daily_data.values())
    total_usd = sum(day_data["USD"] for day_data in daily_data.values())
    total_transactions = sum(day_data["count"] for day_data in daily_data.values())
    
    # Format date range for title
    start_day = start_date.day
    end_day = end_date.day - 1  # Subtract 1 since end_date is exclusive
    month_khmer = get_khmer_month_name(end_date.month)
    year = end_date.year
    
    # Build the report
    report = f"សរុបប្រតិបត្តិការ ថ្ងៃទី {start_day}-{end_day} {month_khmer} {year}\n\n"
    report += "ថ្ងៃ        (៛)              ($)         សរុប(Trans.)\n"
    report += "- - - - - - - - - - - - - -- - - - - - - - - -\n"
    
    # Generate daily rows
    current_date = start_date.date()
    end_date_actual = end_date.date()
    
    while current_date < end_date_actual:
        day_num = current_date.day
        day_data = daily_data.get(current_date, {"KHR": 0, "USD": 0, "count": 0})
        
        khr_formatted = f"{day_data['KHR']:,.0f}"
        usd_formatted = f"{day_data['USD']:,.2f}"
        trans_count = day_data['count']
        
        report += f"{day_num:2}   {khr_formatted:>10}      {usd_formatted:>6}       {trans_count:>2}\n"
        
        current_date = current_date.replace(day=current_date.day + 1) if current_date.day < 31 else current_date.replace(month=current_date.month + 1, day=1)
        if current_date >= end_date_actual:
            break
    
    report += "- - - - - - - - - - - - - -- - - - - - - \n"
    report += f"សរុប: {total_khr:,.0f}   {total_usd:,.2f}   {total_transactions}"
    
    return report