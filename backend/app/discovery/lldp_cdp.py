import asyncio
import logging

from sqlalchemy import select

from app.db import SessionLocal
from app.discovery.snmp_client import bulk_walk_raw
from app.models import Device, Link
from app.ws.manager import manager

logger = logging.getLogger("netmap.lldp_cdp")

RECONCILE_INTERVAL_SECONDS = 45

# LLDP-MIB (indexed by lldpRemTimeMark.lldpRemLocalPortNum.lldpRemIndex)
LLDP_REM_CHASSIS_ID_SUBTYPE = "1.0.8802.1.1.2.1.4.1.1.4"
LLDP_REM_CHASSIS_ID = "1.0.8802.1.1.2.1.4.1.1.5"
LLDP_REM_SYS_NAME = "1.0.8802.1.1.2.1.4.1.1.9"
LLDP_CHASSIS_SUBTYPE_MAC = "4"

# CISCO-CDP-MIB (indexed by ifIndex.cdpCacheDeviceIndex)
CDP_CACHE_ADDRESS = "1.3.6.1.4.1.9.9.23.1.2.1.1.4"
CDP_CACHE_DEVICE_ID = "1.3.6.1.4.1.9.9.23.1.2.1.1.6"


def _format_octets(value: object) -> str:
    """Best-effort decode of an SNMP OCTET STRING: a 6-byte value is treated
    as a MAC, otherwise as UTF-8 text, falling back to hex. Byte-encoding of
    LLDP/CDP fields varies subtly by vendor - this covers the common cases."""
    try:
        raw = value.asOctets()  # type: ignore[attr-defined]
    except AttributeError:
        return str(value)
    if len(raw) == 6:
        return ":".join(f"{b:02X}" for b in raw)
    if len(raw) == 4:
        return ".".join(str(b) for b in raw)
    try:
        return raw.decode("utf-8").strip()
    except UnicodeDecodeError:
        return raw.hex()


async def discover_lldp_neighbors(ip: str, community: str) -> list[dict]:
    """Return neighbors reported by LLDP: [{mac, sys_name}]. Devices that
    don't support LLDP (most consumer switches/APs) return an empty list."""
    subtypes, chassis_ids, sys_names = await asyncio.gather(
        bulk_walk_raw(ip, community, LLDP_REM_CHASSIS_ID_SUBTYPE),
        bulk_walk_raw(ip, community, LLDP_REM_CHASSIS_ID),
        bulk_walk_raw(ip, community, LLDP_REM_SYS_NAME),
    )

    neighbors = []
    for index in chassis_ids:
        subtype = str(subtypes.get(index, ""))
        chassis_id = _format_octets(chassis_ids[index])
        mac = chassis_id if subtype == LLDP_CHASSIS_SUBTYPE_MAC else None
        sys_name = _format_octets(sys_names[index]) if index in sys_names else None
        if mac or sys_name:
            neighbors.append({"mac": mac, "sys_name": sys_name})
    return neighbors


async def discover_cdp_neighbors(ip: str, community: str) -> list[dict]:
    """Return neighbors reported by Cisco Discovery Protocol: [{ip, device_id}]."""
    addresses, device_ids = await asyncio.gather(
        bulk_walk_raw(ip, community, CDP_CACHE_ADDRESS),
        bulk_walk_raw(ip, community, CDP_CACHE_DEVICE_ID),
    )

    neighbors = []
    for index in device_ids:
        ip_str = _format_octets(addresses[index]) if index in addresses else None
        device_id = _format_octets(device_ids[index])
        neighbors.append({"ip": ip_str, "device_id": device_id})
    return neighbors


def _resolve_neighbor(
    neighbor: dict, by_mac: dict[str, Device], by_ip: dict[str, Device], by_hostname: dict[str, Device]
) -> Device | None:
    mac = neighbor.get("mac")
    if mac and mac in by_mac:
        return by_mac[mac]
    ip = neighbor.get("ip")
    if ip and ip in by_ip:
        return by_ip[ip]
    name = (neighbor.get("sys_name") or neighbor.get("device_id") or "").split(".")[0].lower()
    if name and name in by_hostname:
        return by_hostname[name]
    return None


def _upsert_link(session, local: Device, neighbor: Device, existing_links: list[Link]) -> bool:
    for link in existing_links:
        if {link.from_device_id, link.to_device_id} == {local.id, neighbor.id}:
            if link.inferred:
                link.inferred = False
                return True
            return False
    session.add(Link(from_device_id=local.id, to_device_id=neighbor.id, inferred=False))
    return True


async def _reconcile_once() -> bool:
    async with SessionLocal() as session:
        all_devices = (await session.execute(select(Device))).scalars().all()
        snmp_devices = [d for d in all_devices if d.snmp_enabled]
        if not snmp_devices:
            return False

        by_mac = {d.mac.upper(): d for d in all_devices if d.mac}
        by_ip = {d.ip: d for d in all_devices}
        by_hostname = {d.hostname.lower(): d for d in all_devices if d.hostname}
        existing_links = (await session.execute(select(Link))).scalars().all()
        changed = False

        for local in snmp_devices:
            community = local.snmp_community or "public"
            try:
                lldp_neighbors, cdp_neighbors = await asyncio.gather(
                    discover_lldp_neighbors(local.ip, community),
                    discover_cdp_neighbors(local.ip, community),
                )
            except Exception:
                logger.exception("LLDP/CDP discovery failed for %s", local.ip)
                continue

            for neighbor_info in lldp_neighbors + cdp_neighbors:
                neighbor = _resolve_neighbor(neighbor_info, by_mac, by_ip, by_hostname)
                if neighbor and neighbor.id != local.id:
                    if _upsert_link(session, local, neighbor, existing_links):
                        changed = True

        await session.commit()
        return changed


async def reconcile_links_loop() -> None:
    while True:
        try:
            if await _reconcile_once():
                await manager.broadcast({"type": "topology_changed"})
        except Exception:
            logger.exception("LLDP/CDP reconcile pass failed")
        await asyncio.sleep(RECONCILE_INTERVAL_SECONDS)
