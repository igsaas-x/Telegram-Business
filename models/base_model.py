from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from config import Base
from helper import DateUtils


class BaseModel(Base):
    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=DateUtils.now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=DateUtils.now,
        onupdate=DateUtils.now,
        nullable=False,
    )
