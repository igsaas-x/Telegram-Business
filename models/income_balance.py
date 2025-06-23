from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List
from contextlib import contextmanager

from sqlalchemy import Float, String, Column, Integer, DateTime, BigInteger
from sqlalchemy.orm import Session

from config.database_config import Base, SessionLocal


class CurrencyEnum(Enum):
    KHR = "៛"
    USD = "$"

    @classmethod
    def from_symbol(cls, symbol: str) -> Optional[str]:
        for member in cls:
            if member.value == symbol:
                return member.name
        return None


class IncomeBalance(Base):    
    __tablename__ = 'income_balance'
    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    chat_id = Column(BigInteger, nullable=False)
    currency = Column(String(16), nullable=False)
    income_date = Column(DateTime, default=datetime.now, nullable=False)


class IncomeService:
    def __init__(self):
        self._session_factory = SessionLocal

    @contextmanager
    def _get_db(self) -> Session:
        db = self._session_factory()
        try:
            yield db
        finally:
            db.close()

    async def insert_income(self, chat_id: int, amount: float, currency: str) -> IncomeBalance:
        from_symbol = CurrencyEnum.from_symbol(currency)
        currency_code = from_symbol if from_symbol else currency
        current_date = datetime.now()
        
        today_date = datetime(current_date.year, current_date.month, current_date.day)
        tomorrow_date = today_date + timedelta(days=1)
        
        with self._get_db() as db:
            try:
                existing_record = db.query(IncomeBalance).filter(
                    IncomeBalance.chat_id == chat_id,
                    IncomeBalance.currency == currency_code,
                    IncomeBalance.income_date >= today_date,
                    IncomeBalance.income_date < tomorrow_date
                ).first()
                
                if existing_record:
                    existing_record.amount += amount
                    db.commit()
                    db.refresh(existing_record)
                    return existing_record
                
                new_income = IncomeBalance(
                    chat_id=chat_id,
                    amount=amount,
                    currency=currency_code,
                    income_date=current_date
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
            return db.query(IncomeBalance).filter(
                IncomeBalance.id == income_id
            ).first()

    async def get_income_by_chat_id(self, chat_id: int) -> List[IncomeBalance]:
        with self._get_db() as db:
            return db.query(IncomeBalance).filter(
                IncomeBalance.chat_id == chat_id
            ).all()

    async def get_income_by_date_and_chat_id(
        self, 
        chat_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[IncomeBalance]:
        with self._get_db() as db:
            return db.query(IncomeBalance).filter(
                IncomeBalance.chat_id == chat_id,
                IncomeBalance.income_date >= start_date,
                IncomeBalance.income_date < end_date
            ).all()