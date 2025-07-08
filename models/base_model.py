from sqlalchemy import Column, DateTime

from config.database_config import Base
from helper import DateUtils


class BaseModel(Base):
    __abstract__ = True

    created_at = Column(DateTime, default=lambda: DateUtils.now(), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: DateUtils.now(),
        onupdate=lambda: DateUtils.now(),
        nullable=False,
    )
