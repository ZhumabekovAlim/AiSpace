"""Каталог допов к брони (фиксированный набор из кода)."""
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.core.amenities import catalog
from app.models.user import User
from app.schemas.booking import AmenityRead

router = APIRouter(prefix="/amenities", tags=["amenities"])


@router.get("", response_model=list[AmenityRead])
async def list_amenities(_: User = Depends(get_current_user)) -> list[dict]:
    return catalog()
