"""Брони: создать, посмотреть занятость, отменить."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.booking import BookingCreate, BookingRead
from app.services import booking_service

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
async def create_booking(
    payload: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BookingRead:
    try:
        booking = await booking_service.create_booking(
            db,
            user_id=current_user.id,
            room_id=payload.room_id,
            title=payload.title,
            start_time=payload.start_time,
            end_time=payload.end_time,
        )
    except booking_service.RoomNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except booking_service.BookingConflict as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return BookingRead.model_validate(booking)


@router.get("", response_model=list[BookingRead])
async def list_bookings(
    room_id: int | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[BookingRead]:
    bookings = await booking_service.list_bookings(
        db, room_id=room_id, date_from=date_from, date_to=date_to
    )
    return [BookingRead.model_validate(b) for b in bookings]


@router.get("/my", response_model=list[BookingRead])
async def my_bookings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[BookingRead]:
    bookings = await booking_service.list_bookings(db, user_id=current_user.id)
    return [BookingRead.model_validate(b) for b in bookings]


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await booking_service.cancel_booking(
            db,
            booking_id=booking_id,
            requester_id=current_user.id,
            is_admin=current_user.role == UserRole.admin,
        )
    except booking_service.RoomNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc
