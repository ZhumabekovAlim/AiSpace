"""Форматирование времени в таймзоне офиса — для текстов пушей и бота."""
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings

settings = get_settings()
_TZ = ZoneInfo(settings.office_timezone)

_MONTHS = [
    "янв", "фев", "мар", "апр", "мая", "июн",
    "июл", "авг", "сен", "окт", "ноя", "дек",
]


def _local(dt: datetime) -> datetime:
    return dt.astimezone(_TZ)


def fmt_range(start: datetime, end: datetime) -> str:
    s = _local(start)
    e = _local(end)
    return f"{s.day} {_MONTHS[s.month - 1]} {s:%H:%M}–{e:%H:%M}"


def fmt_dt(dt: datetime) -> str:
    d = _local(dt)
    return f"{d.day} {_MONTHS[d.month - 1]} {d:%H:%M}"
