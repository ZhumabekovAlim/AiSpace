"""Разбор фразы в черновик брони. Создание — обычным POST /bookings после подтверждения."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.nl import NLBookingDraft, NLParseRequest
from app.services import nl_service

router = APIRouter(prefix="/nl", tags=["nl"])


@router.post("/parse", response_model=NLBookingDraft)
async def parse(
    payload: NLParseRequest,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NLBookingDraft:
    try:
        return await nl_service.parse_booking(db, payload.text)
    except nl_service.NLServiceError as exc:
        # Внешний сервис недоступен — фронт покажет пустую форму для ручного ввода.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
