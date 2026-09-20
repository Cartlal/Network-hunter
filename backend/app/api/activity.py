from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import ActivityLog
from app.schemas import ActivityOut

router = APIRouter()


@router.get("/api/activity", response_model=list[ActivityOut])
async def list_activity(
    limit: int = Query(50, le=200),
    session: AsyncSession = Depends(get_session),
) -> list[ActivityLog]:
    query = select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(limit)
    return (await session.execute(query)).scalars().all()
