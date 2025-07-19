from datetime import datetime


def shift_report_format(shift_number: int, shift_date: datetime, start_time: datetime, end_time: datetime, 
                       shift_summary: dict, auto_closed: bool = False) -> str:
    """Generate shift report in the specified format"""
    
    # Format date as DD-Month-YYYY (e.g., 17-July-2024)
    formatted_date = shift_date.strftime('%d-%B-%Y')
    
    # Format time in 12-hour format
    start_time_str = start_time.strftime('%I:%M %p')
    end_time_str = end_time.strftime('%I:%M %p') if end_time else "កំពុងបន្ត"
    
    # Build the report
    report = f"#{shift_number}.វេនថ្ងៃទី: {formatted_date} | {start_time_str} - {end_time_str}\n"
    report += "- - - - - - - - - - - - - - - - - - - - - \n"
    report += "សរុប:\n"
    
    # Process currencies from shift summary
    currencies = shift_summary.get("currencies", {})
    
    # Extract KHR and USD data
    khr_data = currencies.get("KHR", {"amount": 0, "count": 0})
    usd_data = currencies.get("USD", {"amount": 0, "count": 0})
    
    # Format KHR line
    khr_amount = int(khr_data["amount"])
    khr_count = khr_data["count"]
    khr_formatted = f"{khr_amount:,.0f}"
    
    # Format USD line
    usd_amount = usd_data["amount"]
    usd_count = usd_data["count"]
    usd_formatted = f"{usd_amount:.2f}"
    
    # Calculate spacing for alignment - ensure pipes align regardless of amount length
    max_amount_length = max(len(khr_formatted), len(usd_formatted))
    
    # Calculate exact spacing needed to align pipes
    khr_spaces_needed = max_amount_length - len(khr_formatted) + 8  # 8 base spaces
    usd_spaces_needed = max_amount_length - len(usd_formatted) + 8  # 8 base spaces
    
    report += f"(៛): {khr_formatted}{' ' * khr_spaces_needed}| ប្រតិបត្តិការណ៍: {khr_count}\n"
    report += f"($): {usd_formatted}{' ' * usd_spaces_needed}| ប្រតិបត្តិការណ៍: {usd_count}\n"
    report += "- - - - - - - - - - - - - - - - - - - - - \n"
    
    # Add note about auto-close if applicable
    if auto_closed and end_time:
        end_time_note = end_time.strftime('%I:%M %p')
        report += f"សំគាល់: របាយការណ៍បិតដោយស្វ័យប្រវត្តិនៅម៉ោង {end_time_note}"
    
    return report


def current_shift_report_format(shift_number: int, shift_date: datetime, start_time: datetime, 
                               shift_summary: dict, duration_hours: int = 0, duration_minutes: int = 0) -> str:
    """Generate current (ongoing) shift report format"""
    
    # Format date as DD-Month-YYYY (e.g., 17-July-2024)
    formatted_date = shift_date.strftime('%d-%B-%Y')
    
    # Format start time in 12-hour format
    start_time_str = start_time.strftime('%I:%M %p')
    
    # Build the report for ongoing shift
    report = f"#{shift_number}.វេនថ្ងៃទី: {formatted_date} | {start_time_str} - កំពុងបន្ត\n"
    report += "- - - - - - - - - - - - - - - - - - - - - \n"
    report += "សរុប:\n"
    
    # Process currencies from shift summary
    currencies = shift_summary.get("currencies", {})
    
    # Extract KHR and USD data
    khr_data = currencies.get("KHR", {"amount": 0, "count": 0})
    usd_data = currencies.get("USD", {"amount": 0, "count": 0})
    
    # Format KHR line
    khr_amount = int(khr_data["amount"])
    khr_count = khr_data["count"]
    khr_formatted = f"{khr_amount:,.0f}"
    
    # Format USD line
    usd_amount = usd_data["amount"]
    usd_count = usd_data["count"]
    usd_formatted = f"{usd_amount:.2f}"
    
    # Calculate spacing for alignment - ensure pipes align regardless of amount length
    max_amount_length = max(len(khr_formatted), len(usd_formatted))
    
    # Calculate exact spacing needed to align pipes
    khr_spaces_needed = max_amount_length - len(khr_formatted) + 8  # 8 base spaces
    usd_spaces_needed = max_amount_length - len(usd_formatted) + 8  # 8 base spaces
    
    report += f"(៛): {khr_formatted}{' ' * khr_spaces_needed}| ប្រតិបត្តិការណ៍: {khr_count}\n"
    report += f"($): {usd_formatted}{' ' * usd_spaces_needed}| ប្រតិបត្តិការណ៍: {usd_count}\n"
    report += "- - - - - - - - - - - - - - - - - - - - - \n"
    
    # Add duration info for ongoing shift
    if duration_hours > 0 or duration_minutes > 0:
        report += f"រយៈពេលវេន: {duration_hours} ម៉ោង {duration_minutes} នាទី"
    
    return report