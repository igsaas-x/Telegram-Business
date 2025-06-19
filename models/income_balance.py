from sqlalchemy import Float, String, Column, Integer, DateTime
from datetime import datetime
from config.database_config import init_db, Base
from enum import Enum


SessionLocal = init_db()
class IncomeBalance(Base):
    __tablename__ = 'income_balance'
    id = Column(Integer, primary_key=True)
    amount = Column(Float, default=True)
    chat_id = Column(Integer, default=False)
    currency = Column(String(16), default=False)
    income_date = Column(DateTime, default=datetime.now)

class IncomeService:
    def __init__(self):
        self.db = SessionLocal()

    async def insert_income(self, chat_id: int, amount: float, currency: str):
        from_symbol = CurrencyEnum.from_symbol(currency)
        currency_code = from_symbol if from_symbol else currency

        try:
            new_income = IncomeBalance(
                chat_id=chat_id,
                amount=amount,
                currency=currency_code,
                income_date=datetime.now()
            )
            self.db.add(new_income)
            self.db.commit()
            self.db.refresh(new_income)
            return new_income
        except Exception as e:
            self.db.rollback()
            raise e

    async def get_income(self, income_id: int):
        return self.db.query(IncomeBalance).filter(
            IncomeBalance.id == income_id
        ).first()

    async def get_income_by_chat_id(self, chat_id: int):
        return self.db.query(IncomeBalance).filter(
            IncomeBalance.chat_id == chat_id
        ).all()

    async def get_income_by_date_and_chat_id(
        self, 
        chat_id: int, 
        start_date: datetime, 
        end_date: datetime
    ):
        return self.db.query(IncomeBalance).filter(
            IncomeBalance.chat_id == chat_id,
            IncomeBalance.income_date >= start_date,
            IncomeBalance.income_date < end_date
        ).all()

    def __del__(self):
        self.db.close()

class CurrencyEnum(Enum):
    KHR = "៛"
    USD = "$"

    @classmethod
    def from_symbol(cls, symbol: str):
        for member in cls:
            if member.value == symbol:
                return member.name
        return None

symbol = "៛"
iso_code = CurrencyEnum.from_symbol(symbol)
symbol = "$"
iso_code = CurrencyEnum.from_symbol(symbol)