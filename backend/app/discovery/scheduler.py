import asyncio
import datetime
import logging
import socket

from sqlalchemy import select

from app.db import SessionLocal
from app.discovery.arp_scan import read_arp_table
from app.discovery.gateway import get_default_gateway
from app.discovery.mdns import mdns_reverse_lookup
from app.discovery.oui import guess_vendor
from app.discovery.ping_sweep import get_local_ip, sweep_subnet
from app.models import ActivityLog, Device, Link, MetricSample
from app.ws.manager import manager

logger = logging.getLogger("netmap.discovery")

SCAN_INTERVAL_SECONDS = 15
HOSTNAME_LOOKUP_TIMEOUT = 0.8


async def _resolve_hostname_dns(ip: str) -> str | None:
    try:
        name, _, _ = await asyncio.wait_for(
            asyncio.to_thread(socket.gethostbyaddr, ip), timeout=HOSTNAME_LOOKUP_TIMEOUT
        )
        return name.split(".")[0]
    except Exception:
        return None


def _guess_device_type(is_gateway: bool, vendor: str | None, hostname: str | None) -> str:
    if is_gateway:
        return "router"
    haystack = f"{vendor or ''} {hostname or ''}".lower()
    if "raspberry" in haystack:
        return "pi"
    if any(term in haystack for term in ("iphone", "android", "phone", "pixel")):
        return "phone"
    if any(term in haystack for term in ("macbook", "laptop", "notebook")):
        return "laptop"
    if any(term in haystack for term in ("printer", "hp", "canon", "epson", "brother")):
        return "printer"
    if any(term in haystack for term in ("pc", "desktop", "workstation")):
        return "pc"
    if any(term in haystack for term in ("dishwasher", "fridge", "refrigerator", "oven", "washer", "thermostat")):
        return "appliance"
    return "unknown"


async def _run_scan_once() -> None:
    gateway_ip = await get_default_gateway()
    latency_by_ip = await sweep_subnet()
    arp_table = await read_arp_table()

    responding_set = set(latency_by_ip) | ({gateway_ip} if gateway_ip else set())
    now = datetime.datetime.utcnow()
    updates: list[dict] = []

    async with SessionLocal() as session:
        existing = (await session.execute(select(Device))).scalars().all()
        by_ip = {d.ip: d for d in existing}

        # Reverse DNS misses most phones/tablets/IoT gear - mDNS catches many
        # of those instead. Only queried for devices still missing a name,
        # so steady-state cycles skip this once everything is resolved.
        unresolved_ips = [ip for ip in responding_set if not (by_ip.get(ip) and by_ip[ip].hostname)]
        mdns_names: dict[str, str] = {}
        if unresolved_ips:
            local_ip = get_local_ip()
            mdns_names = await mdns_reverse_lookup(unresolved_ips, local_ip)

        gateway_device: Device | None = by_ip.get(gateway_ip) if gateway_ip else None

        for ip in responding_set:
            mac = arp_table.get(ip)
            is_gateway = ip == gateway_ip
            device = by_ip.get(ip)

            if device is None:
                hostname = await _resolve_hostname_dns(ip) or mdns_names.get(ip)
                vendor = guess_vendor(mac)
                device = Device(
                    ip=ip,
                    mac=mac,
                    hostname=hostname,
                    vendor=vendor,
                    device_type_guess=_guess_device_type(is_gateway, vendor, hostname),
                    is_gateway=is_gateway,
                    status="online",
                    first_seen=now,
                    last_seen=now,
                )
                session.add(device)
                await session.flush()
                by_ip[ip] = device
                if is_gateway:
                    gateway_device = device
                session.add(
                    ActivityLog(
                        device_id=device.id,
                        event_type="connected",
                        message=f"{hostname or ip} connected",
                        created_at=now,
                    )
                )
            else:
                if device.status != "online":
                    session.add(
                        ActivityLog(
                            device_id=device.id,
                            event_type="connected",
                            message=f"{device.hostname or ip} reconnected",
                            created_at=now,
                        )
                    )
                device.status = "online"
                device.last_seen = now
                if mac and not device.mac:
                    device.mac = mac
                if not device.vendor and device.mac:
                    # Not just for newly-discovered MACs - the OUI table can
                    # gain entries after a device was already recorded, so
                    # retry the guess for any device still missing a vendor.
                    device.vendor = guess_vendor(device.mac)
                if not device.hostname and ip in mdns_names:
                    device.hostname = mdns_names[ip]
                    device.device_type_guess = _guess_device_type(False, device.vendor, device.hostname)

            latency = latency_by_ip.get(ip)
            if latency is not None:
                session.add(MetricSample(device_id=device.id, metric_type="latency_ms", ts=now, value=latency))

            updates.append({"id": device.id, "ip": device.ip, "status": device.status, "last_seen": now})

        for ip, device in by_ip.items():
            if ip not in responding_set and device.status != "offline":
                device.status = "offline"
                session.add(
                    ActivityLog(
                        device_id=device.id,
                        event_type="disconnected",
                        message=f"{device.hostname or ip} disconnected",
                        created_at=now,
                    )
                )
                updates.append({"id": device.id, "ip": device.ip, "status": "offline", "last_seen": device.last_seen})

        links_added = False
        if gateway_device is not None:
            existing_links = (await session.execute(select(Link))).scalars().all()
            # A device already reachable via any link (a real LLDP/CDP-discovered
            # path included) doesn't need the star-topology gateway fallback.
            linked_ids = {link.from_device_id for link in existing_links} | {
                link.to_device_id for link in existing_links
            }
            for ip, device in by_ip.items():
                if device.id != gateway_device.id and device.id not in linked_ids:
                    session.add(Link(from_device_id=gateway_device.id, to_device_id=device.id, inferred=True))
                    links_added = True

        await session.commit()

    if updates:
        await manager.broadcast({"type": "device_status", "devices": updates})
    if links_added:
        await manager.broadcast({"type": "topology_changed"})
    logger.info("Scan complete: %d devices responding", len(responding_set))


async def scan_loop() -> None:
    while True:
        try:
            await _run_scan_once()
        except Exception:
            logger.exception("Discovery scan failed")
        await asyncio.sleep(SCAN_INTERVAL_SECONDS)
