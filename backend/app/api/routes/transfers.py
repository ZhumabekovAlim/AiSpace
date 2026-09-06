"""Передача брони между пользователями + пуши в Telegram на события."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.transfer import BookingTransfer
from app.models.user import User
from app.schemas.transfer import TransferRead, TransferRequestCreate
from app.services import telegram_notify, transfer_service
from app.services.booking_service import BookingConflict
from app.services.transfer_service import (
    TransferError,
    TransferForbidden,
    TransferNotFound,
)
from app.time_utils import fmt_range

router = APIRouter(prefix="/transfers", tags=["transfers"])


async def _notify(user: User, text: str, markup: dict | None = None) -> None:
    if user.telegram_id:
        await telegram_notify.send_message(user.telegram_id, text, reply_markup=markup)


@router.post("", response_model=TransferRead, status_code=status.HTTP_201_CREATED)
async def request_transfer(
    payload: TransferRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TransferRead:
    try:
        transfer = await transfer_service.request_transfer(
            db,
            booking_id=payload.booking_id,
            requester_id=current_user.id,
            new_title=payload.new_title,
            new_comment=payload.new_comment,
            new_amenities=payload.new_amenities,
            new_start_time=payload.new_start_time,
            new_end_time=payload.new_end_time,
        )
    except TransferNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except TransferError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    # Пуш владельцу брони с кнопками подтвердить/отклонить.
    b = transfer.booking
    when = fmt_range(b.start_time, b.end_time)
    text = (
        f"🔄 <b>{transfer.to_user.full_name}</b> просит вашу бронь:\n"
        f"«{b.title}» · {transfer.booking.room.name} · {when}"
    )
    markup = telegram_notify.inline_keyboard(
        [[("✅ Передать", f"transfer:accept:{transfer.id}"),
          ("❌ Отклонить", f"transfer:reject:{transfer.id}")]]
    )
    await _notify(transfer.from_user, text, markup)
    return TransferRead.from_orm_transfer(transfer)


@router.get("", response_model=dict)
async def my_transfers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    incoming, outgoing = await transfer_service.list_for_user(db, current_user.id)
    return {
        "incoming": [TransferRead.from_orm_transfer(t) for t in incoming],
        "outgoing": [TransferRead.from_orm_transfer(t) for t in outgoing],
    }


@router.post("/{transfer_id}/accept", response_model=TransferRead)
async def accept(
    transfer_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TransferRead:
    transfer = await _resolve(db, transfer_id, current_user, "accept")
    await _notify(
        transfer.to_user,
        f"✅ Бронь «{transfer.booking.title}» передана вам "
        f"({transfer.booking.room.name}).",
    )
    return TransferRead.from_orm_transfer(transfer)


@router.post("/{transfer_id}/reject", response_model=TransferRead)
async def reject(
    transfer_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TransferRead:
    transfer = await _resolve(db, transfer_id, current_user, "reject")
    await _notify(
        transfer.to_user,
        f"❌ Запрос на бронь «{transfer.booking.title}» отклонён.",
    )
    return TransferRead.from_orm_transfer(transfer)


@router.post("/{transfer_id}/cancel", response_model=TransferRead)
async def cancel(
    transfer_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TransferRead:
    transfer = await _resolve(db, transfer_id, current_user, "cancel")
    return TransferRead.from_orm_transfer(transfer)


async def _resolve(
    db: AsyncSession, transfer_id: int, user: User, action: str
) -> BookingTransfer:
    fn = {
        "accept": transfer_service.accept_transfer,
        "reject": transfer_service.reject_transfer,
        "cancel": transfer_service.cancel_transfer,
    }[action]
    try:
        return await fn(db, transfer_id=transfer_id, actor_id=user.id)
    except TransferNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except TransferForbidden as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc
    except BookingConflict as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except TransferError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
