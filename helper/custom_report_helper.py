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

    # Format date as DD-MM-YYYY
    date_str = execution_date.strftime("%d-%m-%Y")

    # Header section
    message = f"<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
    message += f"📊 <b>{report_name}</b> {trigger_icon}\n"

    if description:
        message += f"<i>{description}</i>\n"

    message += f"<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
    message += f"📅 <b>កាលបរិច្ឆេទ:</b> {date_str}\n"
    message += f"⚡ <b>ប្រភេទ:</b> {trigger_text}\n\n"

    # Summary section
    message += f"<b>📈 សង្ខេបសរុប</b>\n"
    message += f"<b>{'─' * 30}</b>\n\n"

    # Format currency data
    for currency_code in sorted(currencies.keys()):
        currency_data = currencies[currency_code]
        amount = currency_data["amount"]
        count = currency_data["count"]

        # Format amount based on currency
        if currency_code == "KHR":
            amount_formatted = f"{int(amount):,.0f}"
        else:
            amount_formatted = f"{amount:,.2f}"

        # Currency symbol
        symbol = "៛" if currency_code == "KHR" else "$"

        message += f"💰 <b>{currency_code}</b>\n"
        message += f"   • ចំនួនទឹកប្រាក់: <code>{amount_formatted} {symbol}</code>\n"
        message += f"   • ប្រតិបត្តិការ: <b>{count}</b> លើក\n\n"

    message += f"<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
    message += f"📊 <b>សរុប:</b> {total_count} ប្រតិបត្តិការ"

    return message
