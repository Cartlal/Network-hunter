from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Alert
from app.schemas import AlertOut

router = APIRouter()


@router.get("/api/alerts", response_model=list[AlertOut])
async def list_alerts(
    active_only: bool = Query(False),
    limit: int = Query(50, le=200),
    session: AsyncSession = Depends(get_session),
) -> list[Alert]:
    query = select(Alert).order_by(Alert.created_at.desc()).limit(limit)
    if active_only:
        query = query.where(Alert.resolved_at.is_(None))
    return (await session.execute(query)).scalars().all()
