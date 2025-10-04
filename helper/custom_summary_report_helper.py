from common.enums import CurrencyEnum


def custom_summary_report_with_breakdown(incomes, summary_title: str) -> str:
    """
    Generate summary report with revenue breakdown by source.
    This is used by the custom business bot to show detailed payment source breakdown.
    """
    totals = {currency.name: 0 for currency in CurrencyEnum}
    transaction_counts = {"KHR": 0, "USD": 0}
    source_totals = {}  # Track totals by revenue source

    for income in incomes:
        if income.currency in totals:
            transaction_counts[income.currency] += 1
            totals[income.currency] += income.amount
        else:
            totals[income.currency] = income.amount

        # Aggregate revenue sources if present
        if hasattr(income, 'revenue_sources') and income.revenue_sources:
            for source in income.revenue_sources:
                if source.source_name not in source_totals:
                    source_totals[source.source_name] = 0
                source_totals[source.source_name] += source.amount

    message = f"<b>{summary_title}</b>\n\n"

    # Show currency totals
    for currency in CurrencyEnum:
        code = currency.name
        symbol = currency.value
        total = totals.get(code, 0)
        format_string = "{:,.0f}" if code == "KHR" else "{:,.2f}"
        transaction_count = transaction_counts.get(code, 0)
        message += f"{symbol} ({code}): {format_string.format(total)} | Transactions: {transaction_count}\n"

    # Add revenue breakdown if available
    if source_totals:
        message += "\n📊 <b>Breakdown by Source:</b>\n"
        for source_name, source_amount in sorted(source_totals.items(), key=lambda x: x[1], reverse=True):
            message += f"  • {source_name}: ${source_amount:,.2f}\n"

    return message
