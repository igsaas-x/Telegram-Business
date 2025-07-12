"""Income balance model"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Float,
    String,
    Column,
    Integer,
    DateTime,
    BigInteger,
    Text,
    func,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from config.database_config import get_db_session
from helper import DateUtils
from models.base_model import BaseModel
from models.shift_model import ShiftService


class CurrencyEnum(Enum):
    """Currency enum"""

    KHR = "៛"
    USD = "$"

    @classmethod
    def from_symbol(cls, symbol: str) -> Optional[str]:
        """Get currency from symbol"""
        for member in cls:
            if member.value == symbol:
                return member.name
        return None


class IncomeBalance(BaseModel):
    """Income balance model"""

    __tablename__ = "income_balance"

    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    chat_id = Column(BigInteger, nullable=False)
    currency = Column(String(16), nullable=False)
    original_amount = Column(Float, nullable=False)
    income_date = Column(DateTime, default=lambda: DateUtils.now, nullable=False)
    message_id = Column(BigInteger, nullable=False)
    message = Column(Text, nullable=False)
    # New shift reference
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=True)
    shift = relationship("Shift", back_populates="income_records")

    # DEPRECATED: Keep for backward compatibility during migration
    old_shift = Column(Integer, nullable=True, default=1)
    old_shift_closed = Column(Boolean, nullable=True, default=False)

    trx_id = Column(String(50), nullable=True)


class IncomeService:
    """Income service"""

    def __init__(self):
        self.shift_service = ShiftService()

    async def _ensure_active_shift(self, chat_id: int) -> int:
        """Ensure there's an active shift for the chat, create one if needed"""
        current_shift = await self.shift_service.get_current_shift(chat_id)

        if current_shift:
            return current_shift.id  # type: ignore
        else:
            # No active shift found, create a new one
            new_shift = await self.shift_service.create_shift(chat_id)
            return new_shift.id  # type: ignore

    async def update_shift(self, income_id: int, shift: int):
        """Update shift"""
        with get_db_session() as db:
            income = db.query(IncomeBalance).filter(IncomeBalance.id == income_id)
            if income.first():
                income.update({"shift": shift, "shift_closed": True})
                db.commit()
                return income.first()
            return None

    async def get_last_shift_id(self, chat_id: int) -> IncomeBalance | None:
        """Get last shift ID"""
        with get_db_session() as db:
            last_income = (
                db.query(IncomeBalance)
                .filter(IncomeBalance.chat_id == chat_id)
                .order_by(IncomeBalance.id.desc())
                .first()
            )
            return last_income

    async def insert_income(
        self,
        chat_id: int,
        amount: float,
        currency: str,
        original_amount: float,
        message_id: int,
        message: str,
        trx_id: str | None,
        shift_id: int | None = None,
    ) -> IncomeBalance:
        """Insert income"""
        from_symbol = CurrencyEnum.from_symbol(currency)
        currency_code = from_symbol if from_symbol else currency
        current_date = DateUtils.now()

        # Ensure shift exists - auto-create if needed
        if shift_id is None:
            shift_id = await self._ensure_active_shift(chat_id)

        with get_db_session() as db:
            try:
                new_income = IncomeBalance(
                    chat_id=chat_id,
                    amount=amount,
                    currency=currency_code,
                    income_date=current_date,
                    original_amount=original_amount,
                    message_id=message_id,
                    message=message,
                    trx_id=trx_id,
                    shift_id=shift_id,
                )

                db.add(new_income)
                db.commit()
                db.refresh(new_income)
                return new_income

            except Exception as e:
                db.rollback()
                raise e

    async def get_income(self, income_id: int) -> Optional[IncomeBalance]:
        """Get income"""
        with get_db_session() as db:
            return db.query(IncomeBalance).filter(IncomeBalance.id == income_id).first()

    async def get_income_by_chat_id(self, chat_id: int) -> list[IncomeBalance]:
        """Get income by chat ID"""
        with get_db_session() as db:
            return (
                db.query(IncomeBalance).filter(IncomeBalance.chat_id == chat_id).all()
            )

    async def get_income_by_message_id(self, message_id: int) -> bool:
        """Get income by message ID"""
        with get_db_session() as db:
            return (
                db.query(IncomeBalance)
                .filter(IncomeBalance.message_id == message_id)
                .first()
                is not None
            )

    async def get_income_by_trx_id(self, trx_id: str | None, chat_id: int) -> bool:
        """Get income by transaction ID"""
        if trx_id is None:
            return False
        with get_db_session() as db:
            return (
                db.query(IncomeBalance)
                .filter(
                    IncomeBalance.trx_id == trx_id, IncomeBalance.chat_id == chat_id
                )
                .first()
                is not None
            )

    async def get_last_yesterday_message(
        self, date: datetime
    ) -> Optional[IncomeBalance]:
        """Get last yesterday message"""
        with get_db_session() as db:
            return (
                db.query(IncomeBalance)
                .filter(func.date(IncomeBalance.income_date) == date.date())
                .order_by(IncomeBalance.id.desc())
                .first()
            )

    async def get_income_by_date_and_chat_id(
        self, chat_id: int, start_date: datetime, end_date: datetime
    ) -> list[IncomeBalance]:
        """Get income by date and chat ID"""
        with get_db_session() as db:
            return (
                db.query(IncomeBalance)
                .filter(
                    IncomeBalance.chat_id == chat_id,
                    IncomeBalance.income_date >= start_date,
                    IncomeBalance.income_date < end_date,
                )
                .all()
            )

    async def get_income_by_shift_id(self, shift_id: int) -> list[IncomeBalance]:
        """Get all income records for a specific shift"""
        with get_db_session() as db:
            return (
                db.query(IncomeBalance).filter(IncomeBalance.shift_id == shift_id).all()
            )

    # DEPRECATED: Legacy method for backward compatibility
    async def get_income_chat_id_and_shift(
        self, chat_id: int, shift: int
    ) -> list[IncomeBalance]:
        """Get income by chat ID and shift"""
        current_date = DateUtils.today()
        with get_db_session() as db:
            return (
                db.query(IncomeBalance)
                .filter_by(
                    chat_id=chat_id,
                    old_shift=shift,
                    old_shift_closed=False,
                    income_date=func.date(current_date),
                )
                .all()
            )

    async def get_income_summary_by_date_range(
        self, chat_id: int, start_date: str, end_date: str
    ) -> dict:
        """Get income summary statistics for a date range"""
        start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
        end_datetime = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)

        with get_db_session() as db:
            incomes = (
                db.query(IncomeBalance)
                .filter(
                    IncomeBalance.chat_id == chat_id,
                    IncomeBalance.income_date >= start_datetime,
                    IncomeBalance.income_date < end_datetime,
                )
                .all()
            )

        # Prepare the summary structure
        summary = {"total_amount": 0.0, "count": len(incomes), "by_currency": {}}

        # Calculate totals
        for income in incomes:
            currency = income.currency
            amount = income.amount

            # Initialize currency entry if it doesn't exist
            if currency not in summary["by_currency"]:
                summary["by_currency"][currency] = {"total": 0.0, "count": 0}

            # Add to totals
            summary["by_currency"][currency]["total"] += amount
            summary["by_currency"][currency]["count"] += 1
            summary["total_amount"] += amount

        return summary

    async def get_today_income(self, chat_id: int) -> list[IncomeBalance]:
        """Get all income records for today"""
        today = DateUtils.today()
        tomorrow = today + timedelta(days=1)

        with get_db_session() as db:
            return (
                db.query(IncomeBalance)
                .filter(
                    IncomeBalance.chat_id == chat_id,
                    IncomeBalance.income_date >= today,
                    IncomeBalance.income_date < tomorrow,
                )
                .all()
            )

    async def get_weekly_income(self, chat_id: int) -> list[IncomeBalance]:
        """Get all income records for this week"""
        today = DateUtils.today()
        week_start = today - timedelta(days=today.weekday())

        with get_db_session() as db:
            return (
                db.query(IncomeBalance)
                .filter(
                    IncomeBalance.chat_id == chat_id,
                    IncomeBalance.income_date >= week_start,
                )
                .all()
            )

    async def get_monthly_income(self, chat_id: int) -> list[IncomeBalance]:
        """Get all income records for this month"""
        today = DateUtils.today()
        month_start = today.replace(day=1)

        with get_db_session() as db:
            return (
                db.query(IncomeBalance)
                .filter(
                    IncomeBalance.chat_id == chat_id,
                    IncomeBalance.income_date >= month_start,
                )
                .all()
            )
