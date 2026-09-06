"""Комнаты: список видят все, управление — только админ."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.core.database import get_db
from app.models.room import Room
from app.models.user import User
from app.schemas.room import RoomCreate, RoomRead

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("", response_model=list[RoomRead])
async def list_rooms(
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Room]:
    result = await db.scalars(
        select(Room).where(Room.is_active).order_by(Room.name)
    )
    return list(result)


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
