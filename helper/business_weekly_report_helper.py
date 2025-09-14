from datetime import datetime, timedelta

from .daily_report_helper import get_khmer_month_name


async def business_weekly_transaction_report(chat_id: int, start_date: datetime, end_date: datetime, group_name: str = None) -> str:
    """Generate shift-based weekly transaction report for business groups"""
    
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
    current_date = start_date_obj
    
    # Initialize all dates in range with 0 values
    while current_date <= end_date_obj:
        daily_data[current_date] = {"KHR": 0, "USD": 0, "count": 0}
        current_date = current_date.replace(day=current_date.day + 1) if current_date.day < 31 else current_date.replace(month=current_date.month + 1, day=1)
        if current_date > end_date_obj:
            break
    
    # For each shift, get its income data and aggregate by date
    for shift in shifts:
        shift_date = shift.shift_date
        
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
    start_day = start_date.day
    # Check if end_date is exclusive (00:00:00) or inclusive (23:59:59)
    if end_date.hour == 0 and end_date.minute == 0 and end_date.second == 0:
        # Standard bot format: end_date is exclusive (next day)
        end_day = end_date.day - 1
    else:
        # Business bot format: end_date is inclusive (23:59:59 of actual end day)
        end_day = end_date.day
    month_khmer = get_khmer_month_name(end_date.month)
    year = end_date.year
    
    # Build the report using HTML formatting
    report = f"<b>សរុបប្រតិបត្តិការ ថ្ងៃទី {start_day}-{end_day} {month_khmer} {year}</b>\n"
    report += f"<i>(Based on shifts created on each date)</i>\n"
    
    # Add group name if provided
    if group_name:
        report += f"<b>Group: {group_name}</b>\n"
    
    # Calculate column widths for proper alignment
    # First pass: collect all formatted amounts to determine max widths
    daily_rows = []
    current_date = start_date_obj
    
    while current_date <= end_date_obj:
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
        
        current_date = current_date.replace(day=current_date.day + 1) if current_date.day < 31 else current_date.replace(month=current_date.month + 1, day=1)
        if current_date > end_date_obj:
            break
    
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
    report += f"Tot.: ៛{total_khr_formatted:<10} ${total_usd_formatted:<9} {total_transactions:<12}\n"
    report += "</pre>"
    
    return report