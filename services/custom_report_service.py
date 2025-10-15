import re
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import joinedload

from config import get_db_session
from helper import DateUtils
from helper.logger_utils import force_log
from models import CustomReport, Chat


class CustomReportService:
    """Service for managing and executing custom reports"""

    # Dangerous SQL keywords that should be blocked
    BLOCKED_KEYWORDS = [
        "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE",
        "TRUNCATE", "REPLACE", "GRANT", "REVOKE", "EXEC", "EXECUTE"
    ]

    async def _get_chat_group_id_by_chat_id(self, chat_id: int) -> int | None:
        """Get chat_group.id from telegram chat_id"""
        with get_db_session() as db:
            chat = db.query(Chat).filter(Chat.chat_id == chat_id).first()
            return chat.id if chat else None

    async def get_active_reports_by_chat_id(self, chat_id: int) -> list[CustomReport]:
        """Get all active reports for a chat by telegram chat_id"""
        chat_group_id = await self._get_chat_group_id_by_chat_id(chat_id)
        if not chat_group_id:
            return []
        return await self.get_active_reports_by_chat_group_id(chat_group_id)

    async def get_active_reports_by_chat_group_id(
        self, chat_group_id: int
    ) -> list[CustomReport]:
        """Get all active reports for a chat group"""
        with get_db_session() as db:
            reports = (
                db.query(CustomReport)
                .filter(
                    CustomReport.chat_group_id == chat_group_id,
                    CustomReport.is_active == True,
                )
                .order_by(CustomReport.created_at.desc())
                .all()
            )
            return reports

    async def get_report_by_id(self, report_id: int) -> CustomReport | None:
        """Get a report by ID with eagerly loaded chat_group relationship"""
        with get_db_session() as db:
            report = (
                db.query(CustomReport)
                .options(joinedload(CustomReport.chat_group))  # Eagerly load the relationship
                .filter(CustomReport.id == report_id)
                .first()
            )
            if report:
                db.expunge(report)  # Detach from session but keep loaded data
            return report

    async def get_scheduled_reports(self) -> list[CustomReport]:
        """Get all reports that have scheduling enabled"""
        with get_db_session() as db:
            reports = (
                db.query(CustomReport)
                .options(joinedload(CustomReport.chat_group))  # Eagerly load the relationship
                .filter(
                    CustomReport.is_active == True,
                    CustomReport.schedule_enabled == True,
                    CustomReport.schedule_time.isnot(None),
                )
                .all()
            )
            # Expunge objects from session to make them detached but with loaded relationships
            for report in reports:
                db.expunge(report)
            return reports

    async def create_report(
        self,
        chat_id: int,
        report_name: str,
        sql_query: str,
        description: str | None = None,
        schedule_time: str | None = None,
        schedule_enabled: bool = False,
    ) -> CustomReport | None:
        """Create a new custom report"""
        chat_group_id = await self._get_chat_group_id_by_chat_id(chat_id)
        if not chat_group_id:
            raise ValueError(f"Chat with chat_id {chat_id} not found")

        # Validate SQL query
        if not self._validate_sql_query(sql_query):
            raise ValueError("Invalid SQL query: contains dangerous keywords")

        with get_db_session() as db:
            report = CustomReport(
                chat_group_id=chat_group_id,
                report_name=report_name,
                description=description,
                sql_query=sql_query,
                is_active=True,
                schedule_time=schedule_time,
                schedule_enabled=schedule_enabled,
                created_at=DateUtils.now(),
                updated_at=DateUtils.now(),
            )

            try:
                db.add(report)
                db.commit()
                db.refresh(report)
                force_log(
                    f"Created custom report: {report_name} for chat_group_id {chat_group_id}",
                    "CustomReportService",
                )
                return report
            except Exception as e:
                db.rollback()
                force_log(
                    f"Error creating custom report: {e}",
                    "CustomReportService",
                    "ERROR",
                )
                raise e

    async def update_report(
        self,
        report_id: int,
        report_name: str | None = None,
        sql_query: str | None = None,
        description: str | None = None,
        is_active: bool | None = None,
        schedule_time: str | None = None,
        schedule_enabled: bool | None = None,
    ) -> CustomReport | None:
        """Update an existing custom report"""
        with get_db_session() as db:
            report = db.query(CustomReport).filter(CustomReport.id == report_id).first()

            if not report:
                return None

            # Validate SQL query if provided
            if sql_query and not self._validate_sql_query(sql_query):
                raise ValueError("Invalid SQL query: contains dangerous keywords")

            # Update fields if provided
            if report_name is not None:
                report.report_name = report_name
            if sql_query is not None:
                report.sql_query = sql_query
            if description is not None:
                report.description = description
            if is_active is not None:
                report.is_active = is_active
            if schedule_time is not None:
                report.schedule_time = schedule_time
            if schedule_enabled is not None:
                report.schedule_enabled = schedule_enabled

            report.updated_at = DateUtils.now()

            try:
                db.commit()
                db.refresh(report)
                force_log(
                    f"Updated custom report: {report.report_name} (ID: {report_id})",
                    "CustomReportService",
                )
                return report
            except Exception as e:
                db.rollback()
                force_log(
                    f"Error updating custom report: {e}",
                    "CustomReportService",
                    "ERROR",
                )
                raise e

    async def delete_report(self, report_id: int) -> bool:
        """Delete a custom report"""
        with get_db_session() as db:
            report = db.query(CustomReport).filter(CustomReport.id == report_id).first()

            if not report:
                return False

            try:
                db.delete(report)
                db.commit()
                force_log(
                    f"Deleted custom report: {report.report_name} (ID: {report_id})",
                    "CustomReportService",
                )
                return True
            except Exception as e:
                db.rollback()
                force_log(
                    f"Error deleting custom report: {e}",
                    "CustomReportService",
                    "ERROR",
                )
                raise e

    async def execute_report(self, report_id: int) -> dict[str, Any]:
        """
        Execute a custom report and return aggregated results

        Returns:
            {
                "currencies": {
                    "KHR": {"amount": 8339200, "count": 109},
                    "USD": {"amount": 30834.78, "count": 1179}
                },
                "total_count": 1288,
                "report_name": "Daily Sales"
            }
        """
        with get_db_session() as db:
            # Fetch report with chat_group relationship
            report = (
                db.query(CustomReport)
                .filter(CustomReport.id == report_id)
                .first()
            )

            if not report:
                raise ValueError(f"Report with ID {report_id} not found")

            # Get chat_id from relationship
            chat_id = report.chat_group.chat_id

            # Validate SQL query
            if not self._validate_sql_query(report.sql_query):
                raise ValueError("Invalid SQL query: contains dangerous keywords")

            # Replace :group_id parameter with actual chat_id
            query = report.sql_query.replace(":group_id", str(chat_id))

            force_log(
                f"Executing custom report: {report.report_name} (ID: {report_id})",
                "CustomReportService",
            )

            try:
                # Execute query with timeout
                result = db.execute(
                    text(query).execution_options(timeout=30)
                )
                rows = result.fetchall()

                # Aggregate results by currency
                aggregated = self._aggregate_results(rows)

                # Update last_run_at
                report.last_run_at = DateUtils.now()
                db.commit()

                force_log(
                    f"Successfully executed report {report.report_name}: {len(rows)} rows",
                    "CustomReportService",
                )

                return {
                    **aggregated,
                    "report_name": report.report_name,
                }

            except OperationalError as e:
                force_log(
                    f"Query timeout or execution error for report {report_id}: {e}",
                    "CustomReportService",
                    "ERROR",
                )
                raise ValueError("Query execution timed out or failed")
            except SQLAlchemyError as e:
                force_log(
                    f"Database error executing report {report_id}: {e}",
                    "CustomReportService",
                    "ERROR",
                )
                raise ValueError(f"Database error: {str(e)}")
            except Exception as e:
                force_log(
                    f"Unexpected error executing report {report_id}: {e}",
                    "CustomReportService",
                    "ERROR",
                )
                raise e

    def _validate_sql_query(self, sql_query: str) -> bool:
        """
        Validate SQL query for safety
        - Must contain SELECT
        - Must not contain dangerous keywords
        """
        query_upper = sql_query.upper()

        # Must contain SELECT
        if "SELECT" not in query_upper:
            return False

        # Check for dangerous keywords
        for keyword in self.BLOCKED_KEYWORDS:
            # Use word boundaries to avoid false positives
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, query_upper):
                force_log(
                    f"SQL validation failed: found blocked keyword '{keyword}'",
                    "CustomReportService",
                    "WARN",
                )
                return False

        return True

    def _aggregate_results(self, rows: list) -> dict[str, Any]:
        """
        Aggregate query results by currency

        Expected row structure (from income_balance):
        - amount: float
        - currency: str
        """
        currencies = {}
        total_count = 0

        for row in rows:
            # Handle different row formats (dict or tuple-like)
            if hasattr(row, '_mapping'):
                # SQLAlchemy Row object
                row_dict = dict(row._mapping)
            elif hasattr(row, 'keys'):
                # Dict-like object
                row_dict = dict(row)
            else:
                # Assume it has amount and currency attributes
                row_dict = {"amount": row.amount, "currency": row.currency}

            amount = row_dict.get("amount", 0)
            currency = row_dict.get("currency", "USD")

            if currency not in currencies:
                currencies[currency] = {"amount": 0, "count": 0}

            currencies[currency]["amount"] += amount
            currencies[currency]["count"] += 1
            total_count += 1

        return {"currencies": currencies, "total_count": total_count}
