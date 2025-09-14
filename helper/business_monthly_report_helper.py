from datetime import datetime, timedelta, date

from .daily_report_helper import get_khmer_month_name


async def business_monthly_transaction_report(chat_id: int, start_date: datetime, end_date: datetime, group_name: str = None) -> str:
    """Generate shift-based monthly transaction report for business groups"""
    
    # Import services here to avoid circular imports
    from services.income_balance_service import IncomeService
    from services.shift_service import ShiftService
    
    shift_service = ShiftService()
    income_service = IncomeService()
    
    # Get date range for shifts (convert to date objects)
    start_date_obj = start_date.date()
    end_date_obj = end_date.date()
    
    # Adjust end_date if it's exclusive (00:00:00) to make it inclusive
    if end_date.hour == 0 and end_date.minute == 0 and end_date.second == 0:
        end_date_obj = (end_date - timedelta(days=1)).date()
    
    # Get all shifts within the date range
    shifts = await shift_service.get_shifts_by_date_range(chat_id, start_date_obj, end_date_obj)
    
    # Group shifts by date and summarize daily transaction data based on shifts
    daily_data = {}
    
    # Determine the actual end date for the report
    # If the month hasn't ended yet, only show up to current date
    today = date.today()
    end_date_actual = end_date_obj
    
    # If we're in the same month as start_date and haven't reached end_date yet, 
    # limit to today's date
    if (today.year == start_date.year and 
        today.month == start_date.month and 
        today < end_date_obj):
        end_date_actual = today
    
    # Initialize all dates in range with 0 values
    current_date = start_date_obj
    while current_date <= end_date_actual:
        daily_data[current_date] = {"KHR": 0, "USD": 0, "count": 0}
        current_date = current_date + timedelta(days=1)
    
    # For each shift, get its income data and aggregate by date
    for shift in shifts:
        shift_date = shift.shift_date
        
        # Only process shifts within our actual date range
        if shift_date <= end_date_actual:
            # Get incomes for this specific shift
            shift_incomes = await income_service.get_income_by_shift_id(shift.id)
            
            if shift_incomes:
                for income in shift_incomes:
                    currency = income.currency
                    daily_data[shift_date][currency] += income.amount
                    daily_data[shift_date]["count"] += 1
    
    # Calculate totals
    total_khr = sum(day_data["KHR"] for day_data in daily_data.values())
    total_usd = sum(day_data["USD"] for day_data in daily_data.values())
    total_transactions = sum(day_data["count"] for day_data in daily_data.values())
    
    # Format date range for title
    month_khmer = get_khmer_month_name(start_date.month)
    year = start_date.year
    
    # Build the report using HTML formatting
    report = f"<b>សរុបប្រតិបត្តិការ {month_khmer} {year}</b>\n"
    report += f"<i>(Based on shifts created on each date)</i>\n"
    
    # Add group name if provided
    if group_name:
        report += f"<b>Group: {group_name}</b>\n"
    
    # Calculate column widths for proper alignment
    # First pass: collect all formatted amounts to determine max widths
    daily_rows = []
    current_date = start_date_obj
    
    while current_date <= end_date_actual:
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
        
        current_date = current_date + timedelta(days=1)
    
    # Also consider the totals for width calculation
    total_khr_formatted = f"{total_khr:,.0f}"
    total_usd_formatted = f"{total_usd:,.2f}"
    
    # Create header and table using HTML formatting
    report += "<pre>\n"
    report += f"{'ថ្ងៃ':<3}  {'(៛)':<10} {'($)':<9} {'សរុបចំនួន':<3}\n"
    report += "------------------------------\n"
    
    # Generate daily rows with proper alignment
    for row in daily_rows:
        report += f"{row['day']:<3} {row['khr']:<10} {row['usd']:<9} {row['count']:<3}\n"
    
    report += "------------------------------\n"
    report += f"Tot.: ៛{total_khr_formatted:<10} ${total_usd_formatted:<9} {total_transactions:<3}\n"
    report += "</pre>"
    
    return report