from collections import defaultdict
from datetime import date

from sqlalchemy import func

from config import get_db_session
from helper.logger_utils import force_log
from models.income_balance_model import IncomeBalance
from services.sender_config_service import SenderConfigService


class SenderReportService:
    """Service for generating sender-based reports"""

    def __init__(self):
        self.sender_config_service = SenderConfigService()

    async def generate_daily_report(
        self, chat_id: int, report_date: date | None = None
    ) -> str:
        """
        Generate daily summary report grouped by sender.

        Args:
            chat_id: The chat ID
            report_date: Date to generate report for (defaults to today)

        Returns:
            Formatted report string
        """
        if report_date is None:
            report_date = date.today()

        try:
            # Get configured senders
            configured_senders = await self.sender_config_service.get_senders(chat_id)
            configured_account_numbers = {s.sender_account_number for s in configured_senders}

            # Create mapping of account number to sender name
            sender_names = {
                s.sender_account_number: s.sender_name
                for s in configured_senders
                if s.sender_name
            }

            # Get all transactions for the date
            transactions = await self._get_daily_transactions(chat_id, report_date)

            if not transactions:
                return f"📊 Daily Sender Report - {report_date.strftime('%Y-%m-%d')}\n\n❌ No transactions found for this date."

            # Group transactions by sender
            grouped = self._group_transactions_by_sender(
                transactions, configured_account_numbers
            )

            # Format and return report
            return self._format_report(
                grouped, sender_names, report_date, len(transactions)
            )

        except Exception as e:
            force_log(
                f"Error generating daily report: {e}", "SenderReportService", "ERROR"
            )
            return f"❌ Error generating report: {str(e)}"

    async def _get_daily_transactions(
        self, chat_id: int, report_date: date
    ) -> list[IncomeBalance]:
        """Get all transactions for a specific date"""
        with get_db_session() as session:
            try:
                # Query all transactions for the given date
                transactions = (
                    session.query(IncomeBalance)
                    .filter(
                        IncomeBalance.chat_id == chat_id,
                        func.date(IncomeBalance.income_date) == report_date,
                    )
                    .all()
                )

                # Detach from session
                session.expunge_all()

                return transactions

            except Exception as e:
                force_log(
                    f"Error fetching daily transactions: {e}",
                    "SenderReportService",
                    "ERROR",
                )
                return []

            finally:
                session.close()

    def _group_transactions_by_sender(
        self, transactions: list[IncomeBalance], configured_account_numbers: set[str]
    ) -> dict:
        """
        Group transactions into three categories:
        - configured: Senders in configuration
        - unknown: paid_by not in configuration
        - no_sender: paid_by is NULL
        """
        grouped = {
            "configured": defaultdict(list),
            "unknown": defaultdict(list),
            "no_sender": [],
        }

        for txn in transactions:
            if txn.paid_by is None:
                grouped["no_sender"].append(txn)
            elif txn.paid_by in configured_account_numbers:
                grouped["configured"][txn.paid_by].append(txn)
            else:
                grouped["unknown"][txn.paid_by].append(txn)

        return grouped

    def _calculate_totals(self, transactions: list[IncomeBalance]) -> dict[str, float]:
        """Calculate currency totals for a list of transactions"""
        totals = defaultdict(float)

        for txn in transactions:
            totals[txn.currency] += txn.amount

        return dict(totals)

    def _format_currency_totals(self, totals: dict[str, float]) -> str:
        """Format currency totals as a string"""
        if not totals:
            return "No transactions"

        parts = []
        # Sort by currency for consistent display
        for currency in sorted(totals.keys()):
            amount = totals[currency]
            if currency == "USD":
                parts.append(f"${amount:.2f}")
            elif currency == "KHR":
                parts.append(f"៛{amount:,.0f}")
            else:
                parts.append(f"{amount:,.2f} {currency}")

        return " | ".join(parts)

    def _format_report(
        self,
        grouped: dict,
        sender_names: dict[str, str],
        report_date: date,
        total_transactions: int,
    ) -> str:
        """Format the complete report"""
        lines = []

        # Header
        lines.append(f"📊 Daily Sender Report - {report_date.strftime('%Y-%m-%d')}")
        lines.append(f"Total Transactions: {total_transactions}")
        lines.append("")

        # Section 1: Configured Senders
        if grouped["configured"]:
            lines.append("✅ CONFIGURED SENDERS")
            # lines.append("─" * 40)

            for account_num in sorted(grouped["configured"].keys()):
                transactions = grouped["configured"][account_num]
                totals = self._calculate_totals(transactions)
                sender_name = sender_names.get(account_num, "")

                # Format sender line with HTML
                sender_display = f"*{account_num}"
                if sender_name:
                    sender_display += f" ({sender_name})"

                count = len(transactions)

                # Format each currency amount similar to daily summary
                currency_lines = []
                for currency in sorted(totals.keys()):
                    amount = totals[currency]
                    if currency == "KHR":
                        formatted_amount = f"{amount:,.0f}"
                        currency_lines.append(f"{currency}: {formatted_amount}    | ប្រតិបត្តិការ: {count}")
                    elif currency == "USD":
                        formatted_amount = f"{amount:.2f}"
                        currency_lines.append(f"{currency}: {formatted_amount}    | ប្រតិបត្តិការ: {count}")
                    else:
                        formatted_amount = f"{amount:,.2f}"
                        currency_lines.append(f"{currency}: {formatted_amount}    | ប្រតិបត្តិការ: {count}")

                lines.append(f"\n<b>{sender_display}</b>")
                if currency_lines:
                    lines.append(f"<pre>{chr(10).join(currency_lines)}</pre>")

            lines.append("")

        # Section 2: Unknown Senders (aggregated - includes both unknown and no_sender)
        if grouped["unknown"] or grouped["no_sender"]:
            lines.append("⚠️ Other Senders")
            # lines.append("─" * 40)

            # Combine all unknown transactions (both with unknown account numbers and no sender info)
            all_unknown_transactions = []
            for transactions in grouped["unknown"].values():
                all_unknown_transactions.extend(transactions)
            all_unknown_transactions.extend(grouped["no_sender"])

            totals = self._calculate_totals(all_unknown_transactions)
            count = len(all_unknown_transactions)

            # Format each currency amount similar to daily summary
            currency_lines = []
            for currency in sorted(totals.keys()):
                amount = totals[currency]
                if currency == "KHR":
                    formatted_amount = f"{amount:,.0f}"
                    currency_lines.append(f"{currency}: {formatted_amount}    | ប្រតិបត្តិការ: {count}")
                elif currency == "USD":
                    formatted_amount = f"{amount:.2f}"
                    currency_lines.append(f"{currency}: {formatted_amount}    | ប្រតិបត្តិការ: {count}")
                else:
                    formatted_amount = f"{amount:,.2f}"
                    currency_lines.append(f"{currency}: {formatted_amount}    | ប្រតិបត្តិការ: {count}")

            # lines.append(f"<b>Unknown Senders (not configured)</b>")
            if currency_lines:
                lines.append(f"<pre>{chr(10).join(currency_lines)}</pre>")

            lines.append("")

        # Overall Summary
        lines.append("📈 OVERALL SUMMARY")
        # lines.append("─" * 40)

        # Calculate grand totals
        all_transactions = []
        for txns in grouped["configured"].values():
            all_transactions.extend(txns)
        for txns in grouped["unknown"].values():
            all_transactions.extend(txns)
        all_transactions.extend(grouped["no_sender"])

        grand_totals = self._calculate_totals(all_transactions)
        total_count = len(all_transactions)

        # Format each currency amount similar to daily summary
        currency_lines = []
        for currency in sorted(grand_totals.keys()):
            amount = grand_totals[currency]
            if currency == "KHR":
                formatted_amount = f"{amount:,.0f}"
                currency_lines.append(f"{currency}: {formatted_amount}    | ប្រតិបត្តិការ: {total_count}")
            elif currency == "USD":
                formatted_amount = f"{amount:.2f}"
                currency_lines.append(f"{currency}: {formatted_amount}    | ប្រតិបត្តិការ: {total_count}")
            else:
                formatted_amount = f"{amount:,.2f}"
                currency_lines.append(f"{currency}: {formatted_amount}    | ប្រតិបត្តិការ: {total_count}")

        if currency_lines:
            lines.append(f"<pre>{chr(10).join(currency_lines)}</pre>")

        return "\n".join(lines)

    async def get_sender_summary(
        self, chat_id: int, sender_account_number: str, report_date: date | None = None
    ) -> str:
        """
        Get summary for a specific sender.

        Args:
            chat_id: The chat ID
            sender_account_number: Last 3 digits of account number
            report_date: Date to generate report for (defaults to today)

        Returns:
            Formatted summary string
        """
        if report_date is None:
            report_date = date.today()

        try:
            # Get sender info
            sender = await self.sender_config_service.get_sender_by_account_number(
                chat_id, sender_account_number
            )

            if not sender:
                return f"❌ Sender {sender_account_number} not found"

            # Get transactions for this sender
            transactions = await self._get_sender_transactions(
                chat_id, sender_account_number, report_date
            )

            if not transactions:
                sender_display = f"{sender_account_number}"
                if sender.sender_name:
                    sender_display += f" ({sender.sender_name})"
                return f"📊 Sender Report: {sender_display}\n{report_date.strftime('%Y-%m-%d')}\n\n❌ No transactions found."

            # Calculate totals
            totals = self._calculate_totals(transactions)
            total_str = self._format_currency_totals(totals)

            # Format report
            sender_display = f"{sender_account_number}"
            if sender.sender_name:
                sender_display += f" ({sender.sender_name})"

            lines = [
                f"📊 Sender Report: {sender_display}",
                f"{report_date.strftime('%Y-%m-%d')}",
                "",
                f"Transactions: {len(transactions)}",
                f"Total: {total_str}",
            ]

            return "\n".join(lines)

        except Exception as e:
            force_log(
                f"Error generating sender summary: {e}", "SenderReportService", "ERROR"
            )
            return f"❌ Error generating summary: {str(e)}"

    async def _get_sender_transactions(
        self, chat_id: int, sender_account_number: str, report_date: date
    ) -> list[IncomeBalance]:
        """Get all transactions for a specific sender on a specific date"""
        with get_db_session() as session:
            try:
                transactions = (
                    session.query(IncomeBalance)
                    .filter(
                        IncomeBalance.chat_id == chat_id,
                        IncomeBalance.paid_by == sender_account_number,
                        func.date(IncomeBalance.income_date) == report_date,
                    )
                    .all()
                )

                # Detach from session
                session.expunge_all()

                return transactions

            except Exception as e:
                force_log(
                    f"Error fetching sender transactions: {e}",
                    "SenderReportService",
                    "ERROR",
                )
                return []

            finally:
                session.close()
