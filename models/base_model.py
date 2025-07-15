from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from helper import DateUtils
from config import Base


class BaseModel(Base):
    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=DateUtils.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=DateUtils.now(),
        onupdate=DateUtils.now(),
        nullable=False,
    )
