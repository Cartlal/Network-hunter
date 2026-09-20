import asyncio
import datetime
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal
from app.models import ActivityLog, Device, SecurityFinding
from app.security.scanner import scan_device
from app.security.scoring import compute_score
from app.security.snmp_audit import is_weak_snmp_community
from app.ws.manager import manager

logger = logging.getLogger("netmap.security")

SCAN_INTERVAL_SECONDS = 300  # port scanning is heavier than the 15s device sweep


async def _active_finding(
    session: AsyncSession, device_id: int, finding_type: str, port: int | None
) -> SecurityFinding | None:
    result = await session.execute(
        select(SecurityFinding).where(
            SecurityFinding.device_id == device_id,
            SecurityFinding.finding_type == finding_type,
            SecurityFinding.port == port,
            SecurityFinding.resolved_at.is_(None),
        )
    )
    return result.scalars().first()


async def _scan_insecure_services(
    session: AsyncSession, device: Device, now: datetime.datetime
) -> list[SecurityFinding]:
    new_findings: list[SecurityFinding] = []
    seen_ports: set[int] = set()

    for hit in await scan_device(device.ip):
        service = hit["service"]
        seen_ports.add(service.port)
        existing = await _active_finding(session, device.id, "insecure_service", service.port)
        if existing:
            existing.last_seen = now
            existing.banner = hit["banner"] or existing.banner
            continue
        finding = SecurityFinding(
            device_id=device.id,
            finding_type="insecure_service",
            port=service.port,
            service_name=service.service_name,
            banner=hit["banner"],
            severity=service.severity,
            title=f"{service.service_name} exposed on port {service.port}",
            detail=service.detail,
            remediation=service.remediation,
            first_seen=now,
            last_seen=now,
        )
        session.add(finding)
        new_findings.append(finding)

    # A port that stops answering means the finding no longer reproduces.
    result = await session.execute(
        select(SecurityFinding).where(
            SecurityFinding.device_id == device.id,
            SecurityFinding.finding_type == "insecure_service",
            SecurityFinding.resolved_at.is_(None),
        )
    )
    for finding in result.scalars().all():
        if finding.port not in seen_ports:
            finding.resolved_at = now

    return new_findings


async def _check_weak_snmp(
    session: AsyncSession, device: Device, now: datetime.datetime
) -> list[SecurityFinding]:
    existing = await _active_finding(session, device.id, "weak_snmp_credential", 161)
    is_weak = device.snmp_enabled and device.snmp_supported and is_weak_snmp_community(device.snmp_community)

    if not is_weak:
        if existing:
            existing.resolved_at = now
        return []

    if existing:
        existing.last_seen = now
        return []

    finding = SecurityFinding(
        device_id=device.id,
        finding_type="weak_snmp_credential",
        port=161,
        service_name="SNMP",
        banner=None,
        severity="high",
        title="SNMP answering on a default community string",
        detail=(
            f"This device accepted SNMP requests using the well-known community "
            f"string '{device.snmp_community}'."
        ),
        remediation="Set a unique, non-default SNMP community string in Settings.",
        first_seen=now,
        last_seen=now,
    )
    session.add(finding)
    return [finding]


async def recompute_device_score(session: AsyncSession, device_id: int) -> None:
    device = await session.get(Device, device_id)
    if device is None:
        return
    result = await session.execute(
        select(SecurityFinding.severity).where(
            SecurityFinding.device_id == device_id,
            SecurityFinding.resolved_at.is_(None),
            SecurityFinding.acknowledged_at.is_(None),
        )
    )
    device.security_score = compute_score([row[0] for row in result.all()])


async def run_security_scan_once() -> None:
    now = datetime.datetime.utcnow()
    new_findings: list[SecurityFinding] = []

    async with SessionLocal() as session:
        devices = (await session.execute(select(Device).where(Device.status == "online"))).scalars().all()

        for device in devices:
            new_findings += await _scan_insecure_services(session, device, now)
            new_findings += await _check_weak_snmp(session, device, now)

        await session.flush()
        for device in devices:
            await recompute_device_score(session, device.id)

        for finding in new_findings:
            if finding.severity in ("high", "critical"):
                session.add(
                    ActivityLog(
                        device_id=finding.device_id,
                        event_type="security_finding",
                        message=finding.title,
                        created_at=now,
                    )
                )

        await session.commit()

    logger.info("Security scan complete: %d device(s), %d new finding(s)", len(devices), len(new_findings))
    if new_findings:
        await manager.broadcast({"type": "security_findings_changed"})


async def security_scan_loop() -> None:
    while True:
        try:
            await run_security_scan_once()
        except Exception:
            logger.exception("Security scan pass failed")
        await asyncio.sleep(SCAN_INTERVAL_SECONDS)
