"""Комнаты: список видят все, управление (создание/изменение/архив) — админ."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.core.database import get_db
from app.models.room import Room
from app.models.user import User
from app.schemas.room import RoomCreate, RoomRead, RoomUpdate

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("", response_model=list[RoomRead])
async def list_rooms(
    include_inactive: bool = Query(
        default=False, description="Показывать архивные (только админ)"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Room]:
    stmt = select(Room).order_by(Room.name)
    if not (include_inactive and current_user.role.value == "admin"):
        stmt = stmt.where(Room.is_active)
    return list(await db.scalars(stmt))


@router.post("", response_model=RoomRead, status_code=status.HTTP_201_CREATED)
async def create_room(
    payload: RoomCreate,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Room:
    room = Room(
        name=payload.name,
        capacity=payload.capacity,
        description=payload.description,
    )
    db.add(room)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Комната с таким названием уже существует",
        ) from exc
    await db.refresh(room)
    return room


async def _get_room_or_404(db: AsyncSession, room_id: int) -> Room:
    room = await db.get(Room, room_id)
    if room is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Комната не найдена")
    return room


@router.patch("/{room_id}", response_model=RoomRead)
async def update_room(
    room_id: int,
    payload: RoomUpdate,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Room:
    room = await _get_room_or_404(db, room_id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(room, field, value)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Комната с таким названием уже существует",
        ) from exc
    await db.refresh(room)
    return room


@router.delete("/{room_id}", response_model=RoomRead)
async def archive_room(
    room_id: int,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Room:
    """Мягкое удаление: комната архивируется (is_active=False).

    История броней сохраняется, комнату можно вернуть через PATCH is_active=true.
    """
    room = await _get_room_or_404(db, room_id)
    room.is_active = False
    await db.commit()
    await db.refresh(room)
    return room
