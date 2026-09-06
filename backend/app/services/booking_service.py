"""Бизнес-логика броней: создание с гарантией непересечения, выборки, отмена."""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.room import Room


class BookingError(Exception):
    """Базовая доменная ошибка броней."""


class RoomNotFound(BookingError):
    pass


class BookingConflict(BookingError):
    """Интервал пересекается с существующей бронью этой комнаты."""


async def create_booking(
    db: AsyncSession,
    *,
    user_id: int,
    room_id: int,
    title: str,
    start_time: datetime,
    end_time: datetime,
    comment: str | None = None,
    amenities: list[str] | None = None,
) -> Booking:
    room = await db.get(Room, room_id)
    if room is None or not room.is_active:
        raise RoomNotFound(f"Комната {room_id} не найдена")

    booking = Booking(
        room_id=room_id,
        user_id=user_id,
        title=title,
        start_time=start_time,
        end_time=end_time,
        comment=comment,
        amenities=amenities or [],
    )
    db.add(booking)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        # EXCLUDE-ограничение на уровне БД — единственный надёжный барьер от гонки.
        if "no_overlapping_bookings" in str(exc.orig):
            raise BookingConflict(
                "Комната уже занята на выбранный интервал"
            ) from exc
        raise
    await db.refresh(booking)
    return booking


async def list_bookings(
    db: AsyncSession,
    *,
    room_id: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    user_id: int | None = None,
) -> list[Booking]:
    """Занятость: брони с фильтрами по комнате/периоду/пользователю."""
    stmt = select(Booking)
    if room_id is not None:
        stmt = stmt.where(Booking.room_id == room_id)
    if user_id is not None:
        stmt = stmt.where(Booking.user_id == user_id)
    if date_from is not None:
        stmt = stmt.where(Booking.end_time > date_from)
    if date_to is not None:
        stmt = stmt.where(Booking.start_time < date_to)
    stmt = stmt.order_by(Booking.start_time)
    result = await db.scalars(stmt)
    return list(result)


async def cancel_booking(
    db: AsyncSession, *, booking_id: int, requester_id: int, is_admin: bool
) -> None:
    booking = await db.get(Booking, booking_id)
    if booking is None:
        raise RoomNotFound(f"Бронь {booking_id} не найдена")
    # Обычный пользователь отменяет только свои брони, админ — любые.
    if booking.user_id != requester_id and not is_admin:
        raise PermissionError("Нельзя отменить чужую бронь")
    await db.delete(booking)
    await db.commit()
