from datetime import datetime
from typing import Any


def format_custom_report_result(
    report_name: str,
    results: dict[str, Any],
    execution_date: datetime,
    description: str | None = None,
    trigger_type: str = "manual"
) -> str:
    """
    Format custom report results into a summary message

    Args:
        report_name: Name of the report
        results: Dictionary containing aggregated results
            {
                "currencies": {
                    "KHR": {"amount": 8339200, "count": 109},
                    "USD": {"amount": 30834.78, "count": 1179}
                },
                "total_count": 1288
            }
        execution_date: Date the report was executed
        description: Optional description of the report
        trigger_type: How the report was triggered ("manual" or "auto")

    Returns:
        Formatted HTML message string
    """
    currencies = results.get("currencies", {})
    total_count = results.get("total_count", 0)

    # If no data, return simple message
    if total_count == 0:
        return f"<b>របាយការណ៍:</b> {report_name}\n\nគ្មានទិន្នន័យទេ។"

    # Build the message
    trigger_icon = "🔄" if trigger_type == "auto" else "👤"
    trigger_text = "Auto" if trigger_type == "auto" else "Manual"
    message = f"<b>របាយការណ៍:</b> {report_name} {trigger_icon} ({trigger_text})\n\n"
    message += "——----- summary ———----\n"

    # Format date as DD-MM-YYYY
    date_str = execution_date.strftime("%d-%m-%Y")

    # Show report name and description (if provided)
    report_header = f"📊 <b>{report_name}</b>"
    if description:
        report_header += f" - {description}"
    report_header += f" ({date_str})"
    message += f"{report_header}\n"

    # Format currency data
    currency_lines = []
    for currency_code in sorted(currencies.keys()):
        currency_data = currencies[currency_code]
        amount = currency_data["amount"]
        count = currency_data["count"]

        # Format amount based on currency
        if currency_code == "KHR":
            amount_formatted = f"{int(amount):,.0f}"
        else:
            amount_formatted = f"{amount:.2f}"

        currency_lines.append((currency_code, amount_formatted, count))

    # Calculate spacing for alignment
    max_amount_length = max(len(line[1]) for line in currency_lines) if currency_lines else 0

    # Build aligned output
    aligned_data = ""
    for currency_code, amount_formatted, count in currency_lines:
        spaces_needed = max_amount_length - len(amount_formatted) + 4
        aligned_data += f"{currency_code}: {amount_formatted}{' ' * spaces_needed}| ប្រតិបត្តិការ: {count}\n"

    # Wrap in pre tags for monospace alignment
    message += f"<pre>{aligned_data.rstrip()}</pre>"

    return message
