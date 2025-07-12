from datetime import date
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    DateTime,
    Date,
    BigInteger,
    func,
)
from sqlalchemy.orm import relationship

from config.database_config import get_db_session
from helper import DateUtils
from models.base_model import BaseModel


class Shift(BaseModel):
    """Shift model"""

    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, nullable=False)
    shift_date = Column(Date, nullable=False)
    number = Column(Integer, nullable=False)  # 1, 2, 3... for each day
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)  # NULL if not closed yet
    is_closed = Column(Boolean, nullable=False, default=False)

    # Use string reference instead of direct class reference
    income_records = relationship("IncomeBalance", back_populates="shift")


class ShiftService:
    """Shift service"""

    async def create_shift(self, chat_id: int) -> Shift:
        """Create a new shift starting now"""
        current_time = DateUtils.now()
        with get_db_session() as db:
            last_shift_number = (
                db.query(func.max(Shift.number))
                .filter(
                    Shift.chat_id == chat_id,
                    Shift.shift_date == current_time.date(),
                )
                .scalar()
                or 0
            )

            new_shift = Shift(
                chat_id=chat_id,
                shift_date=current_time.date(),
                number=last_shift_number + 1,
                start_time=current_time,
                is_closed=False,
            )

            db.add(new_shift)
            db.commit()
            db.refresh(new_shift)
            return new_shift

    async def get_current_shift(self, chat_id: int) -> Optional[Shift]:
        """Get the current open shift (regardless of date)"""
        with get_db_session() as db:
            return (
                db.query(Shift)
                .filter(Shift.chat_id == chat_id, Shift.is_closed == False)
                .order_by(Shift.start_time.desc())
                .first()
            )

    async def get_shift_by_id(self, shift_id: int) -> Optional[Shift]:
        """Get shift by ID"""
        with get_db_session() as db:
            return db.query(Shift).filter(Shift.id == shift_id).first()

    async def close_shift(self, shift_id: int) -> Optional[Shift]:
        """Close a shift by setting end_time and is_closed"""
        current_time = DateUtils.now()

        with get_db_session() as db:
            shift = db.query(Shift).filter(Shift.id == shift_id).first()
            if shift and not bool(shift.is_closed):
                shift.end_time = current_time  # type: ignore
                shift.is_closed = True  # type: ignore
                db.commit()
                db.refresh(shift)
                return shift
            return None

    async def get_shifts_by_date_range(
        self, chat_id: int, start_date: date, end_date: date
    ) -> list[Shift]:
        """Get all shifts for a chat within a date range"""
        with get_db_session() as db:
            return (
                db.query(Shift)
                .filter(
                    Shift.chat_id == chat_id,
                    Shift.shift_date >= start_date,
                    Shift.shift_date <= end_date,
                )
                .order_by(Shift.shift_date, Shift.number)
                .all()
            )

    async def get_shifts_by_date(self, chat_id: int, shift_date: date) -> list[Shift]:
        """Get all shifts for a specific date"""
        with get_db_session() as db:
            return (
                db.query(Shift)
                .filter(Shift.chat_id == chat_id, Shift.shift_date == shift_date)
                .order_by(Shift.number)
                .all()
            )

    async def get_recent_closed_shifts(
        self, chat_id: int, limit: int = 1
    ) -> list[Shift]:
        """Get recent closed shifts for a chat"""
        with get_db_session() as db:
            return (
                db.query(Shift)
                .filter(Shift.chat_id == chat_id, Shift.is_closed)
                .order_by(Shift.end_time.desc())
                .limit(limit)
                .all()
            )

    async def get_shift_income_summary(self, shift_id: int) -> dict:
        """Get income summary for a specific shift"""
        from models.income_balance_model import IncomeBalance

        with get_db_session() as db:
            income_records = db.query(IncomeBalance).filter_by(shift_id=shift_id).all()

            if not income_records:
                return {"total_amount": 0.0, "transaction_count": 0, "currencies": {}}

            total_amount = sum(record.amount for record in income_records)
            transaction_count = len(income_records)

            # Group by currency
            currencies = {}
            for record in income_records:
                currency = record.currency or "USD"
                if currency not in currencies:
                    currencies[currency] = {"amount": 0.0, "count": 0}
                currencies[currency]["amount"] += record.amount
                currencies[currency]["count"] += 1

            return {
                "total_amount": total_amount,
                "transaction_count": transaction_count,
                "currencies": currencies,
            }

    async def get_recent_dates_with_shifts(
        self, chat_id: int, days: int = 3
    ) -> list[date]:
        """Get last N dates that have shifts"""
        with get_db_session() as db:
            dates = (
                db.query(Shift.shift_date)
                .filter(Shift.chat_id == chat_id)
                .distinct()
                .order_by(Shift.shift_date.desc())
                .limit(days)
                .all()
            )

            return [d[0] for d in dates]
