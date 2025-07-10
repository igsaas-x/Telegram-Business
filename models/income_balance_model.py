from contextlib import contextmanager
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Generator, Any

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
)
from sqlalchemy.orm import Session

from config.database_config import SessionLocal
from helper import DateUtils
from models.base_model import BaseModel


class CurrencyEnum(Enum):
    KHR = "៛"
    USD = "$"

    @classmethod
    def from_symbol(cls, symbol: str) -> Optional[str]:
        for member in cls:
            if member.value == symbol:
                return member.name
        return None


class IncomeBalance(BaseModel):
    __tablename__ = "income_balance"

    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    chat_id = Column(String(255), nullable=False)
    currency = Column(String(16), nullable=False)
    original_amount = Column(Float, nullable=False)
    income_date = Column(DateTime, default=lambda: DateUtils.now, nullable=False)
    message_id = Column(BigInteger, nullable=False)
    message = Column(Text, nullable=False)
    shift = Column(Integer, nullable=True, default=1)
    shift_closed = Column(Boolean, nullable=True, default=False)
    trx_id = Column(String(50), nullable=True)


class IncomeService:
    def __init__(self):
        self._session_factory = SessionLocal

    @contextmanager
    def _get_db(self) -> Generator[Session, Any, Any]:
        db = self._session_factory()
        try:
            yield db
        finally:
            db.close()

    async def update_shift(self, income_id: int, shift: int):
        with self._get_db() as db:
            income = db.query(IncomeBalance).filter(IncomeBalance.id == income_id)
            if income.first():
                income.update({"shift": shift, "shift_closed": True})
                db.commit()
                return income.first()
            return None

    async def get_last_shift_id(self, chat_id: str) -> type[IncomeBalance] | None:
        with self._get_db() as db:
            last_income = (
                db.query(IncomeBalance)
                .filter(IncomeBalance.chat_id == chat_id)
                .order_by(IncomeBalance.id.desc())
                .first()
            )
            return last_income

    async def insert_income(
            self,
            chat_id: str,
            amount: float,
            currency: str,
            original_amount: float,
            message_id: int,
            message: str,
            trx_id: str | None,
            shift: int,
    ) -> IncomeBalance:
        from_symbol = CurrencyEnum.from_symbol(currency)
        currency_code = from_symbol if from_symbol else currency
        current_date = DateUtils.today()

        with self._get_db() as db:
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
                    shift=shift,
                )

                db.add(new_income)
                db.commit()
                db.refresh(new_income)
                return new_income

            except Exception as e:
                db.rollback()
                raise e

    async def get_income(self, income_id: int) -> Optional[IncomeBalance]:
        with self._get_db() as db:
            return db.query(IncomeBalance).filter(IncomeBalance.id == income_id).first()

    async def get_income_by_chat_id(self, chat_id: str) -> list[type[IncomeBalance]]:
        with self._get_db() as db:
            return (
                db.query(IncomeBalance).filter(IncomeBalance.chat_id == chat_id).all()
            )

    async def get_income_by_message_id(self, message_id: int) -> bool:
        with self._get_db() as db:
            return (
                    db.query(IncomeBalance)
                    .filter(IncomeBalance.message_id == message_id)
                    .first()
                    is not None
            )

    async def get_income_by_trx_id(self, trx_id: str | None) -> bool:
        if trx_id is None:
            return False
        with self._get_db() as db:
            return (
                    db.query(IncomeBalance).filter(IncomeBalance.trx_id == trx_id).first()
                    is not None
            )

    async def get_last_yesterday_message(
            self, date: datetime
    ) -> Optional[IncomeBalance]:
        with self._get_db() as db:
            return (
                db.query(IncomeBalance)
                .filter(func.date(IncomeBalance.income_date) == date.date())
                .order_by(IncomeBalance.id.desc())
                .first()
            )

    async def get_income_by_date_and_chat_id(
            self, chat_id: int, start_date: datetime, end_date: datetime
    ) -> list[type[IncomeBalance]]:
        with self._get_db() as db:
            return (
                db.query(IncomeBalance)
                .filter(
                    IncomeBalance.chat_id == chat_id,
                    IncomeBalance.income_date >= start_date,
                    IncomeBalance.income_date < end_date,
                )
                .all()
            )

    async def get_income_chat_id_and_shift(
            self, chat_id: int, shift: int
    ) -> list[type[IncomeBalance]]:
        current_date = DateUtils.today()
        with self._get_db() as db:
            return (
                db.query(IncomeBalance)
                .filter(
                    IncomeBalance.chat_id == chat_id,
                    IncomeBalance.shift == shift,
                    IncomeBalance.shift_closed == False,
                    func.date(IncomeBalance.income_date) == func.date(current_date),
                )
                .all()
            )

    async def get_income_summary_by_date_range(
            self, chat_id: str, start_date: str, end_date: str
    ) -> dict:
        """
        Get income summary statistics for a date range
        Returns a dictionary with total, count, and breakdown by currency
        """
        # Convert string dates to datetime objects
        start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
        # Add one day to end_date to include the entire end day
        end_datetime = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        
        # Get all income records in the date range
        with self._get_db() as db:
            incomes = (
                db.query(IncomeBalance)
                .filter(
                    IncomeBalance.chat_id == chat_id,
                    IncomeBalance.income_date >= start_datetime,
                    IncomeBalance.income_date < end_datetime
                )
                .all()
            )
            
        # Prepare the summary structure
        summary = {
            "total_amount": 0.0,
            "count": len(incomes),
            "by_currency": {}
        }
        
        # Calculate totals
        for income in incomes:
            currency = income.currency
            amount = income.amount
            
            # Initialize currency entry if it doesn't exist
            if currency not in summary["by_currency"]:
                summary["by_currency"][currency] = {
                    "total": 0.0,
                    "count": 0
                }
                
            # Add to totals
            summary["by_currency"][currency]["total"] += amount
            summary["by_currency"][currency]["count"] += 1
            summary["total_amount"] += amount
            
        return summary
