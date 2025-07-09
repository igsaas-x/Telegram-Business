from contextlib import contextmanager
from datetime import date
from typing import Optional, Generator, Any

from sqlalchemy import (
    Boolean,
    String,
    Column,
    Integer,
    DateTime,
    Date,
    func,
)
from sqlalchemy.orm import Session, relationship

from config.database_config import SessionLocal
from helper import DateUtils
from models.base_model import BaseModel


class Shift(BaseModel):
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True)
    chat_id = Column(String(255), nullable=False)
    shift_date = Column(Date, nullable=False)
    number = Column(Integer, nullable=False)  # 1, 2, 3... for each day
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)  # NULL if not closed yet
    is_closed = Column(Boolean, nullable=False, default=False)
    
    # Relationship to income_balance
    income_records = relationship("IncomeBalance", back_populates="shift")


class ShiftService:
    def __init__(self):
        self._session_factory = SessionLocal

    @contextmanager
    def _get_db(self) -> Generator[Session, Any, Any]:
        db = self._session_factory()
        try:
            yield db
        finally:
            db.close()

    async def create_shift(self, chat_id: str) -> Shift:
        """Create a new shift for today"""
        today = DateUtils.today().date()
        current_time = DateUtils.now()
        
        with self._get_db() as db:
            # Get the highest shift number for today
            last_shift_number = db.query(func.max(Shift.number)).filter(
                Shift.chat_id == chat_id,
                Shift.shift_date == today
            ).scalar() or 0
            
            new_shift = Shift(
                chat_id=chat_id,
                shift_date=today,
                number=last_shift_number + 1,
                start_time=current_time,
                is_closed=False
            )
            
            db.add(new_shift)
            db.commit()
            db.refresh(new_shift)
            return new_shift

    async def get_current_shift(self, chat_id: str) -> Optional[Shift]:
        """Get the current open shift for today"""
        today = DateUtils.today().date()
        
        with self._get_db() as db:
            return db.query(Shift).filter(
                Shift.chat_id == chat_id,
                Shift.shift_date == today,
                Shift.is_closed == False
            ).order_by(Shift.number.desc()).first()

    async def get_shift_by_id(self, shift_id: int) -> Optional[Shift]:
        """Get shift by ID"""
        with self._get_db() as db:
            return db.query(Shift).filter(Shift.id == shift_id).first()

    async def close_shift(self, shift_id: int) -> Optional[Shift]:
        """Close a shift by setting end_time and is_closed"""
        current_time = DateUtils.now()
        
        with self._get_db() as db:
            shift = db.query(Shift).filter(Shift.id == shift_id).first()
            if shift and not shift.is_closed:
                shift.end_time = current_time
                shift.is_closed = True
                db.commit()
                db.refresh(shift)
                return shift
            return None

    async def get_shifts_by_date_range(self, chat_id: str, start_date: date, end_date: date) -> list[Shift]:
        """Get all shifts for a chat within a date range"""
        with self._get_db() as db:
            return db.query(Shift).filter(
                Shift.chat_id == chat_id,
                Shift.shift_date >= start_date,
                Shift.shift_date <= end_date
            ).order_by(Shift.shift_date, Shift.number).all()

    async def get_shift_for_chat_and_date(self, chat_id: str, shift_date: date, shift_number: int) -> Optional[Shift]:
        """Get a specific shift by chat, date, and number"""
        with self._get_db() as db:
            return db.query(Shift).filter(
                Shift.chat_id == chat_id,
                Shift.shift_date == shift_date,
                Shift.number == shift_number
            ).first()