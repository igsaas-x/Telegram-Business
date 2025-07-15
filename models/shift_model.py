from datetime import datetime, date
from sqlalchemy import (
    Boolean,
    Integer,
    DateTime,
    Date,
    BigInteger,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base_model import BaseModel
from models.income_balance_model import IncomeBalance


class Shift(BaseModel):
    __tablename__ = "shifts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    shift_date: Mapped[date] = mapped_column(Date, nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_closed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationship to income_balance
    income_records: Mapped[IncomeBalance] = relationship(
        "IncomeBalance", back_populates="shift"
    )
