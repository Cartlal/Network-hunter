import asyncio
import datetime
import logging

from sqlalchemy import select

from app.db import SessionLocal
from app.discovery.snmp_client import get_system_info, walk_interfaces
from app.models import Device, MetricSample, Port
from app.ws.manager import manager

logger = logging.getLogger("netmap.snmp_poll")

PROBE_INTERVAL_SECONDS = 30
POLL_INTERVAL_SECONDS = 10
DEFAULT_COMMUNITY = "public"


async def _probe_new_devices() -> None:
    """Best-effort auto-detect SNMP support on devices that haven't been
    probed yet, using the common default community string. Devices that
    don't respond are marked snmp_supported=False and left alone - most
    consumer gear falls in this bucket, which is expected."""
    async with SessionLocal() as session:
        devices = (
            (await session.execute(select(Device).where(Device.snmp_supported.is_(None))))
            .scalars()
            .all()
        )
        for device in devices:
            info = await get_system_info(device.ip, DEFAULT_COMMUNITY)
            if info is None:
                device.snmp_supported = False
                continue
            device.snmp_supported = True
            device.snmp_enabled = True
            device.snmp_community = DEFAULT_COMMUNITY
            device.model = info.get("sys_descr")
            device.uptime_seconds = info.get("uptime_seconds")
        await session.commit()


async def _poll_device_ports(session, device: Device) -> list[dict]:
    now = datetime.datetime.utcnow()
    remote_ports = await walk_interfaces(device.ip, device.snmp_community or DEFAULT_COMMUNITY)
    if not remote_ports:
        return []

    existing = {p.if_index: p for p in device.ports}
    updates = []
    for remote in remote_ports:
        port = existing.get(remote["if_index"])
        if port is None:
            port = Port(device_id=device.id, if_index=remote["if_index"], name=remote["name"])
            session.add(port)
            device.ports.append(port)

        rx_bps = tx_bps = 0.0
        if (
            port._last_in_octets is not None
            and port._last_sample_at is not None
            and remote["in_octets"] is not None
        ):
            elapsed = (now - port._last_sample_at).total_seconds()
            if elapsed > 0:
                rx_bps = max(0.0, (remote["in_octets"] - port._last_in_octets) * 8 / elapsed)
                tx_bps = max(0.0, (remote["out_octets"] - port._last_out_octets) * 8 / elapsed)

        port.name = remote["name"]
        port.status = remote["status"]
        port.speed_mbps = remote["speed_mbps"]
        port.rx_bps = rx_bps
        port.tx_bps = tx_bps
        port._last_in_octets = remote["in_octets"]
        port._last_out_octets = remote["out_octets"]
        port._last_sample_at = now

        updates.append(
            {
                "device_id": device.id,
                "if_index": port.if_index,
                "status": port.status,
                "speed_mbps": port.speed_mbps,
                "rx_bps": rx_bps,
                "tx_bps": tx_bps,
            }
        )
    return updates


async def _poll_all_devices() -> None:
    now = datetime.datetime.utcnow()
    async with SessionLocal() as session:
        devices = (
            (await session.execute(select(Device).where(Device.snmp_enabled.is_(True))))
            .scalars()
            .all()
        )
        all_updates: list[dict] = []
        for device in devices:
            try:
                port_updates = await _poll_device_ports(session, device)
            except Exception:
                logger.exception("SNMP poll failed for device %s (%s)", device.id, device.ip)
                continue
            all_updates.extend(port_updates)
            if port_updates:
                total_rx = sum(u["rx_bps"] for u in port_updates)
                total_tx = sum(u["tx_bps"] for u in port_updates)
                session.add(MetricSample(device_id=device.id, metric_type="rx_bps", ts=now, value=total_rx))
                session.add(MetricSample(device_id=device.id, metric_type="tx_bps", ts=now, value=total_tx))
        await session.commit()

    if all_updates:
        await manager.broadcast({"type": "port_metrics", "ports": all_updates})


async def snmp_probe_loop() -> None:
    while True:
        try:
            await _probe_new_devices()
        except Exception:
            logger.exception("SNMP probe pass failed")
        await asyncio.sleep(PROBE_INTERVAL_SECONDS)


async def snmp_poll_loop() -> None:
    while True:
        try:
            await _poll_all_devices()
        except Exception:
            logger.exception("SNMP poll pass failed")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
