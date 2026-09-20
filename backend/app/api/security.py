import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Device, SecurityFinding
from app.schemas import SecurityFindingOut, SecurityOverviewOut
from app.security.engine import recompute_device_score, run_security_scan_once
from app.security.scoring import SEVERITY_PENALTY

router = APIRouter()


@router.get("/api/security/overview", response_model=SecurityOverviewOut)
async def get_security_overview(session: AsyncSession = Depends(get_session)) -> SecurityOverviewOut:
    devices = (await session.execute(select(Device))).scalars().all()
    findings = (
        (
            await session.execute(
                select(SecurityFinding).where(
                    SecurityFinding.resolved_at.is_(None), SecurityFinding.acknowledged_at.is_(None)
                )
            )
        )
        .scalars()
        .all()
    )

    counts = dict.fromkeys(SEVERITY_PENALTY, 0)
    for finding in findings:
        counts[finding.severity] = counts.get(finding.severity, 0) + 1

    network_score = round(sum(d.security_score for d in devices) / len(devices)) if devices else 100
    last_scan_at = max((f.last_seen for f in findings), default=None)

    return SecurityOverviewOut(
        network_score=network_score,
        critical_count=counts.get("critical", 0),
        high_count=counts.get("high", 0),
        medium_count=counts.get("medium", 0),
        low_count=counts.get("low", 0),
        devices_scanned=len(devices),
        last_scan_at=last_scan_at,
    )


@router.get("/api/security/findings", response_model=list[SecurityFindingOut])
async def list_security_findings(
    include_resolved: bool = Query(False),
    include_acknowledged: bool = Query(True),
    session: AsyncSession = Depends(get_session),
) -> list[SecurityFinding]:
    query = select(SecurityFinding).order_by(SecurityFinding.severity, SecurityFinding.last_seen.desc())
    if not include_resolved:
        query = query.where(SecurityFinding.resolved_at.is_(None))
    if not include_acknowledged:
        query = query.where(SecurityFinding.acknowledged_at.is_(None))
    return (await session.execute(query)).scalars().all()


@router.post("/api/security/findings/{finding_id}/acknowledge", response_model=SecurityFindingOut)
async def acknowledge_finding(
    finding_id: int, session: AsyncSession = Depends(get_session)
) -> SecurityFinding:
    finding = await session.get(SecurityFinding, finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    finding.acknowledged_at = datetime.datetime.utcnow()
    await recompute_device_score(session, finding.device_id)
    await session.commit()
    await session.refresh(finding)
    return finding


@router.post("/api/security/rescan")
async def trigger_rescan() -> dict:
    await run_security_scan_once()
    return {"status": "ok"}
