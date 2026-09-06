"""Пользователи (только админ): просмотр списка и управление ролью/блокировкой."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.booking import Booking
from app.models.user import User
from app.schemas.user import UserAdminRead, UserAdminUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserAdminRead])
async def list_users(
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[UserAdminRead]:
    # Число броней на пользователя — одним запросом (LEFT JOIN + GROUP BY).
    stmt = (
        select(User, func.count(Booking.id))
        .outerjoin(Booking, Booking.user_id == User.id)
        .group_by(User.id)
        .order_by(User.id)
    )
    rows = await db.execute(stmt)
    result: list[UserAdminRead] = []
    for user, count in rows.all():
        item = UserAdminRead.model_validate(user)
        item.bookings_count = count
        result.append(item)
    return result


@router.patch("/{user_id}", response_model=UserAdminRead)
async def update_user(
    user_id: int,
    payload: UserAdminUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> UserAdminRead:
    # Защита от самоблокировки/понижения самого себя (иначе можно потерять доступ).
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя менять роль или блокировать самого себя",
        )
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)

    count = await db.scalar(
        select(func.count(Booking.id)).where(Booking.user_id == user.id)
    )
    item = UserAdminRead.model_validate(user)
    item.bookings_count = count or 0
    return item
