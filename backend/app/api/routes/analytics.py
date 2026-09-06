"""Базовая аналитика (только админ)."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.user import User
from app.schemas.analytics import AnalyticsSummary
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("", response_model=AnalyticsSummary)
async def analytics_summary(
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsSummary:
    return await analytics_service.summary(db)
