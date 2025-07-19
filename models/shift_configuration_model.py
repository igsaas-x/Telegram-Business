import json
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, Generator, Any, List

from sqlalchemy import (
    Boolean,
    Integer,
    BigInteger,
    String,
    Text,
    DateTime,
)
from sqlalchemy.orm import Mapped, Session, mapped_column

from config.database_config import SessionLocal
from models.base_model import BaseModel


class ShiftConfiguration(BaseModel):
    __tablename__ = "shift_configurations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    auto_close_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    auto_close_times: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON array of times (e.g., ["08:00", "16:00", "23:59"])

    # Shift naming/numbering preferences
    shift_name_prefix: Mapped[str] = mapped_column(
        String(50), nullable=True, default="Shift"
    )
    reset_numbering_daily: Mapped[bool | None] = mapped_column(
        Boolean, nullable=False, default=True
    )

    # Timezone for this chat (optional)
    timezone: Mapped[str | None] = mapped_column(
        String(50), nullable=True, default="Asia/Phnom_Penh"
    )

    # Last job run tracking
    last_job_run: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    def get_auto_close_times_list(self) -> List[str]:
        """Get auto close times as a list of time strings"""
        if not self.auto_close_times:
            return []
        try:
            return json.loads(self.auto_close_times)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_auto_close_times_list(self, times: List[str]) -> None:
        """Set auto close times from a list of time strings"""
        if times:
            self.auto_close_times = json.dumps(times)
        else:
            self.auto_close_times = None


class ShiftConfigurationService:
    def __init__(self):
        self._session_factory = SessionLocal

    @contextmanager
    def _get_db(self) -> Generator[Session, Any, Any]:
        db = self._session_factory()
        try:
            yield db
        finally:
            db.close()

    async def get_configuration(self, chat_id: int) -> Optional[ShiftConfiguration]:
        """Get configuration if exists"""
        with self._get_db() as db:
            config = (
                db.query(ShiftConfiguration)
                .filter(ShiftConfiguration.chat_id == chat_id)
                .first()
            )

            return config

    async def update_auto_close_settings(
        self, chat_id: int, enabled: bool, auto_close_times: Optional[List[str]] = None
    ) -> Optional[ShiftConfiguration]:
        """Update auto close settings for a chat"""
        with self._get_db() as db:
            config = await self.get_configuration(chat_id)
            if not config:
                return None

            # Refresh the object in this session
            config = db.merge(config)

            config.auto_close_enabled = enabled

            # Set multiple auto close times
            if auto_close_times:
                # Validate time formats and set the times
                validated_times = []
                for time_str in auto_close_times:
                    # Validate time format (HH:MM or HH:MM:SS)
                    try:
                        time_parts = time_str.split(":")
                        if len(time_parts) == 2:
                            time_parts.append("00")  # Add seconds if not provided
                        elif len(time_parts) != 3:
                            continue  # Skip invalid format

                        # Validate ranges
                        hour = int(time_parts[0])
                        minute = int(time_parts[1])
                        second = int(time_parts[2])

                        if 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59:
                            validated_times.append(
                                f"{hour:02d}:{minute:02d}:{second:02d}"
                            )
                    except (ValueError, IndexError):
                        continue  # Skip invalid times

                config.set_auto_close_times_list(validated_times)
            else:
                config.set_auto_close_times_list([])

            db.commit()
            db.refresh(config)
            return config

    async def update_shift_preferences(
        self,
        chat_id: int,
        shift_name_prefix: Optional[str] = None,
        reset_numbering_daily: Optional[bool] = None,
        timezone: Optional[str] = None,
    ) -> Optional[ShiftConfiguration]:
        """Update shift naming and numbering preferences"""
        with self._get_db() as db:
            config = await self.get_configuration(chat_id)
            if not config:
                return None

            # Refresh the object in this session
            config = db.merge(config)

            if shift_name_prefix is not None:
                config.shift_name_prefix = shift_name_prefix
            if reset_numbering_daily is not None:
                config.reset_numbering_daily = reset_numbering_daily
            if timezone is not None:
                config.timezone = timezone

            db.commit()
            db.refresh(config)
            return config

    async def update_last_job_run(self, chat_id: int, job_run_time) -> None:
        """Update the last job run timestamp for a chat configuration"""
        with self._get_db() as db:
            config = (
                db.query(ShiftConfiguration)
                .filter(ShiftConfiguration.chat_id == chat_id)
                .first()
            )

            if config:
                config.last_job_run = job_run_time
                db.commit()
