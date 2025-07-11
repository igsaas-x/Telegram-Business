from contextlib import contextmanager
from datetime import date
from typing import Optional, Generator, Any, Dict, List
from dataclasses import dataclass

from sqlalchemy import (
    Boolean,
    String,
    Column,
    Integer,
    DateTime,
    Date,
    func,
    Index,
)
from sqlalchemy.orm import Session, relationship, joinedload

from config.database_config import SessionLocal
from helper import DateUtils
from models.base_model import BaseModel


class Shift(BaseModel):
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True)
    chat_id = Column(
        String(255), nullable=False, index=True
    )  # Add index for performance
    shift_date = Column(Date, nullable=False, index=True)  # Add index for date queries
    number = Column(Integer, nullable=False)  # 1, 2, 3... for each day
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)  # NULL if not closed yet
    is_closed = Column(
        Boolean, nullable=False, default=False, index=True
    )  # Add index for filtering

    # Relationship to income_balance with lazy loading optimization
    income_records = relationship(
        "IncomeBalance", back_populates="shift", lazy="select"
    )

    # Add composite indexes for common query patterns
    __table_args__ = (
        Index("idx_chat_id_closed", "chat_id", "is_closed"),
        Index("idx_chat_id_date", "chat_id", "shift_date"),
        Index("idx_chat_id_date_number", "chat_id", "shift_date", "number"),
    )


@dataclass
class ShiftSummary:
    """Data class for shift summary to avoid repeated calculations"""

    total_amount: float
    transaction_count: int
    currencies: Dict[str, Dict[str, float]]


class ShiftService:
    def __init__(self):
        self._session_factory = SessionLocal
        self._current_shift_cache: Dict[str, Optional[Shift]] = {}  # Simple cache

    @contextmanager
    def _get_db(self) -> Generator[Session, Any, Any]:
        db = self._session_factory()
        try:
            yield db
        finally:
            db.close()

    def _invalidate_cache(self, chat_id: str) -> None:
        """Invalidate cache for a specific chat"""
        self._current_shift_cache.pop(chat_id, None)

    async def create_shift(self, chat_id: str) -> Shift:
        """Create a new shift starting now - optimized with single query"""
        current_time = DateUtils.now()
        shift_date = current_time.date()

        with self._get_db() as db:
            # Get the highest shift number for this chat in a single query
            last_shift_number = (
                db.query(func.coalesce(func.max(Shift.number), 0))
                .filter(Shift.chat_id == chat_id)
                .scalar()
            )

            new_shift = Shift(
                chat_id=chat_id,
                shift_date=shift_date,
                number=last_shift_number + 1,
                start_time=current_time,
                is_closed=False,
            )

            db.add(new_shift)
            db.commit()
            db.refresh(new_shift)

            # Invalidate cache after creating new shift
            self._invalidate_cache(chat_id)

            return new_shift

    async def get_current_shift(self, chat_id: str) -> Optional[Shift]:
        """Get the current open shift with caching"""
        # Check cache first
        if chat_id in self._current_shift_cache:
            return self._current_shift_cache[chat_id]

        with self._get_db() as db:
            shift = (
                db.query(Shift)
                .filter(Shift.chat_id == chat_id, Shift.is_closed == False)
                .order_by(Shift.start_time.desc())
                .first()
            )

            # Cache the result
            self._current_shift_cache[chat_id] = shift
            return shift

    async def get_shift_by_id(self, shift_id: int) -> Optional[Shift]:
        """Get shift by ID - optimized query"""
        with self._get_db() as db:
            return db.query(Shift).filter(Shift.id == shift_id).first()

    async def close_shift(self, shift_id: int) -> Optional[Shift]:
        """Close a shift by setting end_time and is_closed - optimized transaction"""
        current_time = DateUtils.now()

        with self._get_db() as db:
            # Use update() for better performance than fetch + modify
            updated_rows = (
                db.query(Shift)
                .filter(
                    Shift.id == shift_id,
                    Shift.is_closed == False,  # Only update if not already closed
                )
                .update(
                    {"end_time": current_time, "is_closed": True},
                    synchronize_session=False,
                )
            )

            if updated_rows > 0:
                db.commit()
                # Get the updated shift and invalidate cache
                shift = db.query(Shift).filter(Shift.id == shift_id).first()
                if shift:
                    self._invalidate_cache(str(shift.chat_id))
                return shift

            return None

    async def get_shifts_by_date_range(
        self, chat_id: str, start_date: date, end_date: date
    ) -> List[Shift]:
        """Get all shifts for a chat within a date range - optimized with indexes"""
        with self._get_db() as db:
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

    async def get_shifts_by_date(self, chat_id: str, shift_date: date) -> List[Shift]:
        """Get all shifts for a specific date - optimized with composite index"""
        with self._get_db() as db:
            return (
                db.query(Shift)
                .filter(Shift.chat_id == chat_id, Shift.shift_date == shift_date)
                .order_by(Shift.number)
                .all()
            )

    async def get_recent_closed_shifts(
        self, chat_id: str, limit: int = 1
    ) -> List[Shift]:
        """Get recent closed shifts for a chat - optimized query"""
        with self._get_db() as db:
            return (
                db.query(Shift)
                .filter(Shift.chat_id == chat_id, Shift.is_closed == True)
                .order_by(Shift.end_time.desc())
                .limit(limit)
                .all()
            )

    async def get_shift_income_summary(self, shift_id: int) -> ShiftSummary:
        """Get income summary for a specific shift - optimized with aggregation"""
        with self._get_db() as db:
            from models.income_balance_model import IncomeBalance

            # Use database aggregation instead of Python loops
            result = (
                db.query(
                    func.sum(IncomeBalance.amount).label("total_amount"),
                    func.count(IncomeBalance.id).label("transaction_count"),
                    IncomeBalance.currency,
                )
                .filter(IncomeBalance.shift_id == shift_id)
                .group_by(IncomeBalance.currency)
                .all()
            )

            if not result:
                return ShiftSummary(
                    total_amount=0.0, transaction_count=0, currencies={}
                )

            total_amount = sum(r.total_amount or 0 for r in result)
            transaction_count = sum(r.transaction_count or 0 for r in result)

            # Build currency breakdown from aggregated results
            currencies = {}
            for r in result:
                currency = r.currency or "USD"
                currencies[currency] = {
                    "amount": float(r.total_amount or 0),
                    "count": int(r.transaction_count or 0),
                }

            return ShiftSummary(
                total_amount=float(total_amount),
                transaction_count=int(transaction_count),
                currencies=currencies,
            )

    async def get_recent_dates_with_shifts(
        self, chat_id: str, days: int = 3
    ) -> List[date]:
        """Get last N dates that have shifts - optimized query"""
        with self._get_db() as db:
            # Use DISTINCT directly in the query for better performance
            dates = (
                db.query(Shift.shift_date)
                .filter(Shift.chat_id == chat_id)
                .distinct()
                .order_by(Shift.shift_date.desc())
                .limit(days)
                .all()
            )

            return [d[0] for d in dates]

    async def get_shifts_with_income_summary(
        self, chat_id: str, start_date: date, end_date: date
    ) -> List[Dict]:
        """Get shifts with pre-calculated income summaries - batch optimization"""
        with self._get_db() as db:
            from models.income_balance_model import IncomeBalance

            # Use JOIN and aggregation to get shift + summary in one query
            results = (
                db.query(
                    Shift,
                    func.coalesce(func.sum(IncomeBalance.amount), 0).label(
                        "total_amount"
                    ),
                    func.count(IncomeBalance.id).label("transaction_count"),
                )
                .outerjoin(IncomeBalance, Shift.id == IncomeBalance.shift_id)
                .filter(
                    Shift.chat_id == chat_id,
                    Shift.shift_date >= start_date,
                    Shift.shift_date <= end_date,
                )
                .group_by(Shift.id)
                .order_by(Shift.shift_date, Shift.number)
                .all()
            )

            return [
                {
                    "shift": result[0],
                    "summary": ShiftSummary(
                        total_amount=float(result.total_amount),
                        transaction_count=int(result.transaction_count),
                        currencies={},  # Could be extended to include currency breakdown
                    ),
                }
                for result in results
            ]

    async def bulk_close_shifts(self, shift_ids: List[int]) -> int:
        """Close multiple shifts efficiently - batch operation"""
        if not shift_ids:
            return 0

        current_time = DateUtils.now()

        with self._get_db() as db:
            updated_rows = (
                db.query(Shift)
                .filter(Shift.id.in_(shift_ids), Shift.is_closed == False)
                .update(
                    {"end_time": current_time, "is_closed": True},
                    synchronize_session=False,
                )
            )

            if updated_rows > 0:
                db.commit()
                # Clear cache for affected chats
                affected_chats = (
                    db.query(Shift.chat_id)
                    .filter(Shift.id.in_(shift_ids))
                    .distinct()
                    .all()
                )

                for chat_id_tuple in affected_chats:
                    self._invalidate_cache(chat_id_tuple[0])

            return updated_rows
