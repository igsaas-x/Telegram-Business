from datetime import datetime

from .daily_report_helper import get_khmer_month_name


def monthly_transaction_report(incomes, start_date: datetime, end_date: datetime) -> str:
    """Generate monthly transaction report in format similar to weekly report"""
    
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
    month_khmer = get_khmer_month_name(start_date.month)
    year = start_date.year
    
    # Build the report
    report = f"សរុបប្រតិបត្តិការ {month_khmer} {year}\n\n"
    
    # Calculate column widths for proper alignment
    # First pass: collect all formatted amounts to determine max widths
    daily_rows = []
    current_date = start_date.date()
    end_date_actual = end_date.date()
    
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
        
        # Move to next day
        try:
            if current_date.day < 28:  # Safe increment
                current_date = current_date.replace(day=current_date.day + 1)
            else:
                # Handle end of month
                next_month = current_date.month + 1 if current_date.month < 12 else 1
                next_year = current_date.year if current_date.month < 12 else current_date.year + 1
                current_date = current_date.replace(year=next_year, month=next_month, day=1)
        except ValueError:
            # If we can't increment (e.g., Feb 29 on non-leap year), move to next month
            next_month = current_date.month + 1 if current_date.month < 12 else 1
            next_year = current_date.year if current_date.month < 12 else current_date.year + 1
            current_date = current_date.replace(year=next_year, month=next_month, day=1)
        
        if current_date >= end_date_actual:
            break
    
    # Calculate maximum widths for alignment
    max_khr_width = max(len(row['khr']) for row in daily_rows) if daily_rows else 8
    max_usd_width = max(len(row['usd']) for row in daily_rows) if daily_rows else 6
    
    # Also consider the totals for width calculation
    total_khr_formatted = f"{total_khr:,.0f}"
    total_usd_formatted = f"{total_usd:,.2f}"
    max_khr_width = max(max_khr_width, len(total_khr_formatted))
    max_usd_width = max(max_usd_width, len(total_usd_formatted))
    
    # Create header with proper spacing
    report += f"ថ្ងៃ  {'(៛)':>{max_khr_width}}  {'($)':>{max_usd_width}}  សរុប(Trans.)\n"
    report += "- - - - - - - - - - - - - - - - - - - - - \n"
    
    # Generate daily rows with proper alignment
    for row in daily_rows:
        report += f"{row['day']:2}  {row['khr']:>{max_khr_width}}  {row['usd']:>{max_usd_width}}  {row['count']:>2}\n"
    
    report += "- - - - - - - - - - - - - - - - - - - - - \n"
    report += f"សរុប: {total_khr_formatted:>{max_khr_width}}  {total_usd_formatted:>{max_usd_width}}  {total_transactions}"
    
    return report