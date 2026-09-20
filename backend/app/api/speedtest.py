from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import SpeedTestResult
from app.schemas import SpeedTestResultOut
from app.speedtest.runner import run_speed_test

router = APIRouter()


@router.post("/api/speedtest/run", response_model=SpeedTestResultOut)
async def trigger_speed_test() -> SpeedTestResult:
    try:
        return await run_speed_test()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Speed test failed: {exc}") from exc


@router.get("/api/speedtest/latest", response_model=SpeedTestResultOut | None)
async def get_latest_speed_test(session: AsyncSession = Depends(get_session)) -> SpeedTestResult | None:
    result = await session.execute(select(SpeedTestResult).order_by(SpeedTestResult.tested_at.desc()).limit(1))
    return result.scalars().first()


@router.get("/api/speedtest/history", response_model=list[SpeedTestResultOut])
async def get_speed_test_history(
    limit: int = Query(20, le=100), session: AsyncSession = Depends(get_session)
) -> list[SpeedTestResult]:
    result = await session.execute(
        select(SpeedTestResult).order_by(SpeedTestResult.tested_at.desc()).limit(limit)
    )
    return result.scalars().all()
