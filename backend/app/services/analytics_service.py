"""Базовая аналитика по броням для админки.

Считаем агрегатами в SQL, где это просто; популярность допов (ARRAY-колонка) —
в Python из лёгкой выборки, чтобы не усложнять запрос unnest'ом.
"""
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.room import Room
from app.models.user import User
from app.schemas.analytics import AnalyticsSummary, DayCount, NameCount

_WINDOW_DAYS = 14


async def summary(db: AsyncSession) -> AnalyticsSummary:
    now = datetime.now(timezone.utc)

    total_bookings = await db.scalar(select(func.count(Booking.id))) or 0
    upcoming = (
        await db.scalar(
            select(func.count(Booking.id)).where(Booking.end_time >= now)
        )
        or 0
    )
    active_rooms = (
        await db.scalar(select(func.count(Room.id)).where(Room.is_active)) or 0
    )
    total_users = await db.scalar(select(func.count(User.id))) or 0

    # Суммарные часы бронирований.
    seconds = await db.scalar(
        select(
            func.coalesce(
                func.sum(
                    func.extract("epoch", Booking.end_time - Booking.start_time)
                ),
                0,
            )
        )
    )
    total_hours = round(float(seconds or 0) / 3600, 1)

    # Броней по комнатам.
    per_room_rows = await db.execute(
        select(Room.name, func.count(Booking.id))
        .outerjoin(Booking, Booking.room_id == Room.id)
        .group_by(Room.id)
        .order_by(func.count(Booking.id).desc())
    )
    per_room = [NameCount(label=n, count=c) for n, c in per_room_rows.all()]

    # Топ-5 пользователей по числу броней.
    top_rows = await db.execute(
        select(User.full_name, func.count(Booking.id))
        .join(Booking, Booking.user_id == User.id)
        .group_by(User.id)
        .order_by(func.count(Booking.id).desc())
        .limit(5)
    )
    top_users = [NameCount(label=n, count=c) for n, c in top_rows.all()]

    # Брони по дням: окно ±неделя вокруг сегодня (в UTC), с заполнением нулей.
    # Так видно и недавнюю историю, и предстоящую загрузку.
    start = (now - timedelta(days=_WINDOW_DAYS // 2)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end = start + timedelta(days=_WINDOW_DAYS)
    day_expr = func.date(Booking.start_time)
    day_rows = await db.execute(
        select(day_expr, func.count(Booking.id))
        .where(Booking.start_time >= start, Booking.start_time < end)
        .group_by(day_expr)
    )
    counts = {str(d): c for d, c in day_rows.all()}
    per_day = []
    for i in range(_WINDOW_DAYS):
        d = (start + timedelta(days=i)).date().isoformat()
        per_day.append(DayCount(date=d, count=counts.get(d, 0)))

    # Популярность допов — из лёгкой выборки массивов.
    amenity_lists = await db.scalars(select(Booking.amenities))
    counter: Counter[str] = Counter()
    for lst in amenity_lists:
        counter.update(lst or [])
    amenities = [
        NameCount(label=k, count=v) for k, v in counter.most_common()
    ]

    return AnalyticsSummary(
        total_bookings=total_bookings,
        upcoming_bookings=upcoming,
        active_rooms=active_rooms,
        total_users=total_users,
        total_hours=total_hours,
        per_room=per_room,
        per_day=per_day,
        top_users=top_users,
        amenities=amenities,
    )
