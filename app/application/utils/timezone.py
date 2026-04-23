from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone


def local_now() -> datetime:
    """Return current datetime in the configured local timezone.

    Uses ZoneInfo when available, falls back to a fixed UTC offset
    parsed from DEFAULT_TIMEZONE_OFFSET (default -5 for Lima/Bogota).
    This avoids depending on system or package tzdata being installed.
    """
    tz_name = os.environ.get("DEFAULT_TIMEZONE", "America/Lima")
    try:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
        return datetime.now(ZoneInfo(tz_name))
    except Exception:
        offset_hours = int(os.environ.get("DEFAULT_TIMEZONE_OFFSET", "-5"))
        return datetime.now(timezone(timedelta(hours=offset_hours)))


def local_today() -> date:
    return local_now().date()
