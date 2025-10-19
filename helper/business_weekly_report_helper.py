from datetime import datetime, timedelta

from .daily_report_helper import get_khmer_month_name


async def custom_business_weekly_report(chat_id: int, start_date: datetime, end_date: datetime, group_name: str = None) -> str:
    """Generate custom weekly report with Shift 1 and Shift 2 columns (only 2 shifts allowed)"""

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

    # Group shifts by date - only allow Shift 1 and Shift 2
    daily_data = {}
    current_date = start_date_obj

    # Initialize all dates in range
    while current_date <= end_date_obj:
        daily_data[current_date] = {
            "shift1": {"KHR": 0, "USD": 0},
            "shift2": {"KHR": 0, "USD": 0}
        }
        current_date += timedelta(days=1)

    # Process shifts - only use shift number 1 and 2
    for shift in shifts:
        shift_date = shift.shift_date
        shift_number = shift.number

        # Only process shift 1 and shift 2
        if shift_number not in [1, 2]:
            continue

        shift_key = "shift1" if shift_number == 1 else "shift2"

        # Get incomes for this specific shift
        shift_incomes = await income_service.get_income_by_shift_id(shift.id)

        if shift_incomes:
            for income in shift_incomes:
                currency = income.currency
                if currency in ["KHR", "USD"]:
                    daily_data[shift_date][shift_key][currency] += income.amount

    # Calculate totals
    total_shift1_khr = sum(day_data["shift1"]["KHR"] for day_data in daily_data.values())
    total_shift1_usd = sum(day_data["shift1"]["USD"] for day_data in daily_data.values())
    total_shift2_khr = sum(day_data["shift2"]["KHR"] for day_data in daily_data.values())
    total_shift2_usd = sum(day_data["shift2"]["USD"] for day_data in daily_data.values())

    # Format date range for title
    start_day = start_date.day
    if end_date.hour == 0 and end_date.minute == 0 and end_date.second == 0:
        end_day = end_date.day - 1
    else:
        end_day = end_date.day
    month_khmer = get_khmer_month_name(end_date.month)
    year = end_date.year

    # Build the report using HTML formatting with two separate tables
    report = f"<b>សរុបប្រតិបត្តិការ ថ្ងៃទី {start_day}-{end_day} {month_khmer} {year}</b>\n"

    # Add group name if provided
    if group_name:
        report += f"<b>Group: {group_name}</b>\n\n"

    # Build Shift 1 table
    report += "<b>វេនទី 1 (Shift 1)</b>\n"
    report += "<pre>\n"
    report += f"{'Date':<12} {'USD':<9} {'KHR':<10}\n"
    report += "=" * 33 + "\n"

    # Generate Shift 1 daily rows
    current_date = start_date_obj
    while current_date <= end_date_obj:
        day_data = daily_data.get(current_date, {"shift1": {"KHR": 0, "USD": 0}, "shift2": {"KHR": 0, "USD": 0}})

        date_str = current_date.strftime('%d-%m-%Y')
        s1_usd = f"{day_data['shift1']['USD']:.0f}"
        s1_khr = f"{day_data['shift1']['KHR']:.0f}"

        report += f"{date_str:<12} {s1_usd:<9} {s1_khr:<10}\n"

        current_date += timedelta(days=1)

    # Add Shift 1 total row
    report += "=" * 33 + "\n"
    total_s1_usd = f"{total_shift1_usd:.0f}"
    total_s1_khr = f"{total_shift1_khr:.0f}"
    report += f"{'Total':<12} {total_s1_usd:<9} {total_s1_khr:<10}\n"
    report += "</pre>\n"

    # Build Shift 2 table
    report += "<b>វេនទី 2 (Shift 2)</b>\n"
    report += "<pre>\n"
    report += f"{'Date':<12} {'USD':<9} {'KHR':<10}\n"
    report += "=" * 33 + "\n"

    # Generate Shift 2 daily rows
    current_date = start_date_obj
    while current_date <= end_date_obj:
        day_data = daily_data.get(current_date, {"shift1": {"KHR": 0, "USD": 0}, "shift2": {"KHR": 0, "USD": 0}})

        date_str = current_date.strftime('%d-%m-%Y')
        s2_usd = f"{day_data['shift2']['USD']:.0f}"
        s2_khr = f"{day_data['shift2']['KHR']:.0f}"

        report += f"{date_str:<12} {s2_usd:<9} {s2_khr:<10}\n"

        current_date += timedelta(days=1)

    # Add Shift 2 total row
    report += "=" * 33 + "\n"
    total_s2_usd = f"{total_shift2_usd:.0f}"
    total_s2_khr = f"{total_shift2_khr:.0f}"
    report += f"{'Total':<12} {total_s2_usd:<9} {total_s2_khr:<10}\n"
    report += "</pre>"

    return report


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