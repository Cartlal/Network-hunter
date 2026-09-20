import asyncio
import datetime
import logging

from sqlalchemy import select

from app.alerts.notifier import notify
from app.db import SessionLocal
from app.models import ActivityLog, Alert, Device, MetricSample, Port
from app.ws.manager import manager

logger = logging.getLogger("netmap.alerts")

EVAL_INTERVAL_SECONDS = 20
DEVICE_DOWN_CRITICAL_AFTER = datetime.timedelta(minutes=5)
HIGH_LATENCY_THRESHOLD_MS = 150
HIGH_BANDWIDTH_UTILIZATION = 0.85


async def _active_alert(session, device_id: int, rule_type: str) -> Alert | None:
    result = await session.execute(
        select(Alert).where(
            Alert.device_id == device_id, Alert.rule_type == rule_type, Alert.resolved_at.is_(None)
        )
    )
    return result.scalars().first()


async def _raise_alert(session, device: Device, rule_type: str, severity: str, message: str) -> Alert:
    alert = Alert(device_id=device.id, rule_type=rule_type, severity=severity, message=message)
    session.add(alert)
    session.add(ActivityLog(device_id=device.id, event_type="alert", message=message))
    await session.flush()
    return alert


async def _resolve_alert(session, alert: Alert, device: Device, recovery_message: str) -> None:
    alert.resolved_at = datetime.datetime.utcnow()
    session.add(ActivityLog(device_id=device.id, event_type="alert_resolved", message=recovery_message))


async def _check_device_down(session, devices: list[Device]) -> list[Alert]:
    new_alerts = []
    now = datetime.datetime.utcnow()
    for device in devices:
        existing = await _active_alert(session, device.id, "device_down")
        name = device.hostname or device.ip

        if device.status == "offline":
            if existing is None:
                alert = await _raise_alert(session, device, "device_down", "warning", f"{name} is unreachable")
                new_alerts.append(alert)
            elif existing.severity == "warning" and now - device.last_seen > DEVICE_DOWN_CRITICAL_AFTER:
                existing.severity = "critical"
                existing.message = f"{name} has been down for over {DEVICE_DOWN_CRITICAL_AFTER.seconds // 60} minutes"
                new_alerts.append(existing)
        elif existing is not None:
            await _resolve_alert(session, existing, device, f"{name} is back online")

    return new_alerts


async def _latest_metric(session, device_id: int, metric_type: str) -> float | None:
    result = await session.execute(
        select(MetricSample.value)
        .where(MetricSample.device_id == device_id, MetricSample.metric_type == metric_type)
        .order_by(MetricSample.ts.desc())
        .limit(1)
    )
    row = result.first()
    return row[0] if row else None


async def _check_high_latency(session, devices: list[Device]) -> list[Alert]:
    new_alerts = []
    for device in devices:
        if device.status != "online":
            continue
        latency = await _latest_metric(session, device.id, "latency_ms")
        existing = await _active_alert(session, device.id, "high_latency")
        name = device.hostname or device.ip

        if latency is not None and latency > HIGH_LATENCY_THRESHOLD_MS:
            if existing is None:
                alert = await _raise_alert(
                    session, device, "high_latency", "warning", f"{name} latency is high ({latency:.0f} ms)"
                )
                new_alerts.append(alert)
        elif existing is not None:
            await _resolve_alert(session, existing, device, f"{name} latency back to normal")

    return new_alerts


async def _check_high_bandwidth(session, devices: list[Device]) -> list[Alert]:
    new_alerts = []
    for device in devices:
        if not device.snmp_enabled or device.status != "online":
            continue
        ports_result = await session.execute(select(Port).where(Port.device_id == device.id))
        ports = ports_result.scalars().all()
        capacity_bps = sum(p.speed_mbps for p in ports) * 1_000_000
        if capacity_bps <= 0:
            continue
        usage_bps = sum(p.rx_bps + p.tx_bps for p in ports)
        utilization = usage_bps / capacity_bps
        existing = await _active_alert(session, device.id, "high_bandwidth")
        name = device.hostname or device.ip

        if utilization > HIGH_BANDWIDTH_UTILIZATION:
            if existing is None:
                alert = await _raise_alert(
                    session,
                    device,
                    "high_bandwidth",
                    "warning",
                    f"{name} bandwidth utilization is high ({utilization * 100:.0f}%)",
                )
                new_alerts.append(alert)
        elif existing is not None:
            await _resolve_alert(session, existing, device, f"{name} bandwidth utilization back to normal")

    return new_alerts


async def _evaluate_once() -> None:
    async with SessionLocal() as session:
        devices = (await session.execute(select(Device))).scalars().all()
        changed = []
        changed += await _check_device_down(session, devices)
        changed += await _check_high_latency(session, devices)
        changed += await _check_high_bandwidth(session, devices)
        await session.commit()

    if changed:
        await notify(changed)
        await manager.broadcast({"type": "alerts_changed"})


async def alert_evaluation_loop() -> None:
    while True:
        try:
            await _evaluate_once()
        except Exception:
            logger.exception("Alert evaluation pass failed")
        await asyncio.sleep(EVAL_INTERVAL_SECONDS)
