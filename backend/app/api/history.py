import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import MetricSample
from app.schemas import MetricSampleOut

router = APIRouter()

RANGE_TO_TIMEDELTA = {
    "15m": datetime.timedelta(minutes=15),
    "1h": datetime.timedelta(hours=1),
    "6h": datetime.timedelta(hours=6),
    "24h": datetime.timedelta(hours=24),
    "7d": datetime.timedelta(days=7),
}


@router.get("/api/devices/{device_id}/metrics", response_model=list[MetricSampleOut])
async def get_device_metrics(
    device_id: int,
    metric_type: str = Query(..., pattern="^(latency_ms|rx_bps|tx_bps)$"),
    range: str = Query("1h", pattern="^(15m|1h|6h|24h|7d)$"),
    session: AsyncSession = Depends(get_session),
) -> list[MetricSample]:
    if range not in RANGE_TO_TIMEDELTA:
        raise HTTPException(status_code=400, detail="Invalid range")
    since = datetime.datetime.utcnow() - RANGE_TO_TIMEDELTA[range]
    result = await session.execute(
        select(MetricSample)
        .where(
            MetricSample.device_id == device_id,
            MetricSample.metric_type == metric_type,
            MetricSample.ts >= since,
        )
        .order_by(MetricSample.ts)
    )
    return result.scalars().all()
