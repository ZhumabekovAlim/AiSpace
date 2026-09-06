from pydantic import BaseModel


class NameCount(BaseModel):
    label: str
    count: int


class DayCount(BaseModel):
    date: str  # YYYY-MM-DD
    count: int


class AnalyticsSummary(BaseModel):
    total_bookings: int
    upcoming_bookings: int
    active_rooms: int
    total_users: int
    total_hours: float
    per_room: list[NameCount]
    per_day: list[DayCount]  # непрерывный ряд за последние 14 дней
    top_users: list[NameCount]
    amenities: list[NameCount]  # label = id допа (фронт подставит иконку)
