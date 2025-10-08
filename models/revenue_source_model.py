import typing

if typing.TYPE_CHECKING:
    from models.income_balance_model import IncomeBalance

from sqlalchemy import (
    Float,
    String,
    Integer,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base_model import BaseModel


class RevenueSource(BaseModel):
    """Store breakdown of revenue by payment source (Cash, Bank Card, Ctrip, Agoda, etc.)"""
    __tablename__ = "revenue_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    income_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("income_balance.id"), nullable=False
    )
    source_name: Mapped[str] = mapped_column(String(50), nullable=False)  # Cash, Bank Card, Ctrip, Agoda, etc.
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(16), nullable=False, default="USD")
    shift: Mapped[str | None] = mapped_column(String(10), nullable=True)  # Internal shift identifier (e.g., "C", "D")

    # Relationship back to income
    income: Mapped["IncomeBalance"] = relationship("IncomeBalance", back_populates="revenue_sources")
