from datetime import datetime
from sqlalchemy import Column, DateTime
from config.database_config import Base


class BaseModel(Base):
    __abstract__ = True

    created_at = Column(DateTime, default=lambda: datetime.now(), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(),
        onupdate=lambda: datetime.now(),
        nullable=False,
    )
