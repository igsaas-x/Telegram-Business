from datetime import UTC, datetime
from sqlalchemy import Column, DateTime
from config.database_config import Base


class BaseModel(Base):
    __abstract__ = True

    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
