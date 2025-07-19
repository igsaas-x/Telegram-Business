from config import get_db_session
from models import ShiftConfiguration


class ShiftConfigurationService:
    async def get_configuration(self, chat_id: int) -> ShiftConfiguration | None:
        with get_db_session() as db:
            config = (
                db.query(ShiftConfiguration)
                .filter(ShiftConfiguration.chat_id == chat_id)
                .first()
            )

            return config

    async def update_auto_close_settings(
        self, chat_id: int, enabled: bool, auto_close_times: list[str] = []
    ) -> ShiftConfiguration | None:
        with get_db_session() as db:
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
        shift_name_prefix: str | None = None,
        reset_numbering_daily: bool | None = None,
        timezone: str | None = None,
    ) -> ShiftConfiguration | None:
        with get_db_session() as db:
            config = await self.get_configuration(chat_id)
            if not config:
                return None

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
        with get_db_session() as db:
            config = (
                db.query(ShiftConfiguration)
                .filter(ShiftConfiguration.chat_id == chat_id)
                .first()
            )

            if config:
                config.last_job_run = job_run_time
                db.commit()
