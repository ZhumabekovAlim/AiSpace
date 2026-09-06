"""Передача брони между пользователями.

Сценарий: юзеру B нужна комната, занятая B... то есть A. B запрашивает бронь у A
(опционально с желаемыми изменениями). A подтверждает — бронь переходит к B с
применением изменений (тема/комментарий/допы/время в той же комнате). Изменение
времени проходит ту же проверку непересечения (EXCLUDE) — при конфликте отказ.
"""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.booking import Booking
from app.models.transfer import BookingTransfer, TransferStatus
from app.services.booking_service import BookingConflict


class TransferError(Exception):
    pass


class TransferNotFound(TransferError):
    pass


class TransferForbidden(TransferError):
    pass


async def request_transfer(
    db: AsyncSession,
    *,
    booking_id: int,
    requester_id: int,
    new_title: str | None = None,
    new_comment: str | None = None,
    new_amenities: list[str] | None = None,
    new_start_time: datetime | None = None,
    new_end_time: datetime | None = None,
) -> BookingTransfer:
    booking = await db.get(Booking, booking_id)
    if booking is None:
        raise TransferNotFound("Бронь не найдена")
    if booking.user_id == requester_id:
        raise TransferError("Это уже ваша бронь")

    # Не плодим дубли: один активный запрос от этого юзера на эту бронь.
    existing = await db.scalar(
        select(BookingTransfer).where(
            BookingTransfer.booking_id == booking_id,
            BookingTransfer.to_user_id == requester_id,
            BookingTransfer.status == TransferStatus.pending,
        )
    )
    if existing is not None:
        raise TransferError("Запрос на эту бронь уже отправлен")

    transfer = BookingTransfer(
        booking_id=booking_id,
        from_user_id=booking.user_id,
        to_user_id=requester_id,
        status=TransferStatus.pending,
        new_title=new_title,
        new_comment=new_comment,
        new_amenities=new_amenities,
        new_start_time=new_start_time,
        new_end_time=new_end_time,
    )
    db.add(transfer)
    await db.commit()
    return await _load(db, transfer.id)


async def accept_transfer(
    db: AsyncSession, *, transfer_id: int, actor_id: int
) -> BookingTransfer:
    transfer = await _load(db, transfer_id)
    _ensure_pending(transfer)
    if transfer.from_user_id != actor_id:
        raise TransferForbidden("Подтвердить может только владелец брони")

    booking = transfer.booking

    # Прочие ожидающие запросы выбираем ДО мутации брони: иначе SELECT вызовет
    # autoflush изменённого (возможно конфликтного) времени вне try/except.
    others = list(
        await db.scalars(
            select(BookingTransfer).where(
                BookingTransfer.booking_id == booking.id,
                BookingTransfer.id != transfer.id,
                BookingTransfer.status == TransferStatus.pending,
            )
        )
    )

    now = datetime.now(timezone.utc)
    booking.user_id = transfer.to_user_id
    if transfer.new_title is not None:
        booking.title = transfer.new_title
    if transfer.new_comment is not None:
        booking.comment = transfer.new_comment
    if transfer.new_amenities is not None:
        booking.amenities = transfer.new_amenities
    if transfer.new_start_time is not None and transfer.new_end_time is not None:
        booking.start_time = transfer.new_start_time
        booking.end_time = transfer.new_end_time

    transfer.status = TransferStatus.accepted
    transfer.resolved_at = now
    for o in others:  # прочие запросы на эту бронь больше не актуальны
        o.status = TransferStatus.cancelled
        o.resolved_at = now

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        if "no_overlapping_bookings" in str(exc.orig):
            raise BookingConflict(
                "Новое время пересекается с другой бронью комнаты"
            ) from exc
        raise
    return await _load(db, transfer_id)


async def reject_transfer(
    db: AsyncSession, *, transfer_id: int, actor_id: int
) -> BookingTransfer:
    return await _resolve_negative(
        db, transfer_id, actor_id, TransferStatus.rejected, owner=True
    )


async def cancel_transfer(
    db: AsyncSession, *, transfer_id: int, actor_id: int
) -> BookingTransfer:
    return await _resolve_negative(
        db, transfer_id, actor_id, TransferStatus.cancelled, owner=False
    )


async def list_for_user(
    db: AsyncSession, user_id: int
) -> tuple[list[BookingTransfer], list[BookingTransfer]]:
    """(incoming — где я владелец и жду решения, outgoing — что я запросил)."""
    stmt = (
        select(BookingTransfer)
        .options(
            joinedload(BookingTransfer.booking).joinedload(Booking.room),
            joinedload(BookingTransfer.from_user),
            joinedload(BookingTransfer.to_user),
        )
        .where(
            (BookingTransfer.from_user_id == user_id)
            | (BookingTransfer.to_user_id == user_id)
        )
        .order_by(BookingTransfer.created_at.desc())
    )
    rows = list(await db.scalars(stmt))
    incoming = [t for t in rows if t.from_user_id == user_id]
    outgoing = [t for t in rows if t.to_user_id == user_id]
    return incoming, outgoing


async def _resolve_negative(
    db: AsyncSession,
    transfer_id: int,
    actor_id: int,
    status: TransferStatus,
    *,
    owner: bool,
) -> BookingTransfer:
    transfer = await _load(db, transfer_id)
    _ensure_pending(transfer)
    allowed = transfer.from_user_id if owner else transfer.to_user_id
    if actor_id != allowed:
        raise TransferForbidden("Недостаточно прав для этого действия")
    transfer.status = status
    transfer.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    return await _load(db, transfer_id)


def _ensure_pending(transfer: BookingTransfer) -> None:
    if transfer.status != TransferStatus.pending:
        raise TransferError(f"Запрос уже обработан ({transfer.status.value})")


async def _load(db: AsyncSession, transfer_id: int) -> BookingTransfer:
    transfer = await db.scalar(
        select(BookingTransfer)
        .options(
            joinedload(BookingTransfer.booking).joinedload(Booking.room),
            joinedload(BookingTransfer.from_user),
            joinedload(BookingTransfer.to_user),
        )
        .where(BookingTransfer.id == transfer_id)
    )
    if transfer is None:
        raise TransferNotFound("Запрос не найден")
    return transfer
