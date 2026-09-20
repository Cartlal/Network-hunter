import asyncio
import logging

from pysnmp.hlapi.v3arch.asyncio import (
    CommunityData,
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    bulk_walk_cmd,
    get_cmd,
)

logger = logging.getLogger("netmap.snmp")

SNMP_TIMEOUT = 1.5
SNMP_PORT = 161

OID_SYS_DESCR = "1.3.6.1.2.1.1.1.0"
OID_SYS_UPTIME = "1.3.6.1.2.1.1.3.0"
OID_SYS_NAME = "1.3.6.1.2.1.1.5.0"

OID_IF_DESCR = "1.3.6.1.2.1.2.2.1.2"
OID_IF_OPER_STATUS = "1.3.6.1.2.1.2.2.1.8"
OID_IF_NAME = "1.3.6.1.2.1.31.1.1.1.1"
OID_IF_HIGH_SPEED = "1.3.6.1.2.1.31.1.1.1.15"  # Mbps
OID_IF_HC_IN_OCTETS = "1.3.6.1.2.1.31.1.1.1.6"
OID_IF_HC_OUT_OCTETS = "1.3.6.1.2.1.31.1.1.1.10"

OPER_STATUS_UP = 1


def _engine() -> SnmpEngine:
    return SnmpEngine()


async def _target(ip: str) -> UdpTransportTarget:
    return await UdpTransportTarget.create((ip, SNMP_PORT), timeout=SNMP_TIMEOUT, retries=0)


async def get_system_info(ip: str, community: str) -> dict | None:
    """GET sysDescr/sysUpTime/sysName. Returns None if the device doesn't
    respond (no SNMP support, wrong community, or firewalled) - this is the
    expected/common case on consumer gear."""
    try:
        error_indication, error_status, _, var_binds = await get_cmd(
            _engine(),
            CommunityData(community, mpModel=1),
            await _target(ip),
            ContextData(),
            ObjectType(ObjectIdentity(OID_SYS_DESCR)),
            ObjectType(ObjectIdentity(OID_SYS_UPTIME)),
            ObjectType(ObjectIdentity(OID_SYS_NAME)),
        )
    except Exception:
        logger.debug("SNMP get_system_info failed for %s", ip, exc_info=True)
        return None

    if error_indication or error_status:
        return None

    sys_descr, sys_uptime, sys_name = (str(vb[1]) for vb in var_binds)
    try:
        uptime_seconds = int(sys_uptime) / 100
    except (ValueError, TypeError):
        uptime_seconds = None

    return {"sys_descr": sys_descr, "uptime_seconds": uptime_seconds, "sys_name": sys_name}


async def bulk_walk_indexed(ip: str, community: str, base_oid: str) -> dict[str, str]:
    """Walk a MIB subtree, returning {index_suffix: value}. index_suffix is
    the OID tail after base_oid - a single component for simple tables
    (ifTable) or a dotted composite for multi-index tables (LLDP-MIB's
    lldpRemTable is indexed by timeMark.localPortNum.remIndex)."""
    results: dict[str, str] = {}
    try:
        async for error_indication, error_status, _, var_binds in bulk_walk_cmd(
            _engine(),
            CommunityData(community, mpModel=1),
            await _target(ip),
            ContextData(),
            0,
            10,
            ObjectType(ObjectIdentity(base_oid)),
            lexicographicMode=False,
        ):
            if error_indication or error_status:
                break
            for oid, value in var_binds:
                oid_str = str(oid)
                if not oid_str.startswith(base_oid + "."):
                    return results
                results[oid_str[len(base_oid) + 1 :]] = str(value)
    except Exception:
        logger.debug("SNMP walk failed for %s (%s)", ip, base_oid, exc_info=True)
    return results


async def _bulk_walk(ip: str, community: str, base_oid: str) -> dict[str, str]:
    """Walk a single-index MIB subtree, returning {last_oid_component: value}."""
    indexed = await bulk_walk_indexed(ip, community, base_oid)
    return {key.rsplit(".", 1)[-1]: value for key, value in indexed.items()}


async def bulk_walk_raw(ip: str, community: str, base_oid: str) -> dict[str, object]:
    """Like bulk_walk_indexed, but keeps the raw pysnmp value objects instead
    of stringifying them - needed for OCTET STRING fields (e.g. LLDP chassis
    IDs) where the byte encoding matters and str() would mangle it."""
    results: dict[str, object] = {}
    try:
        async for error_indication, error_status, _, var_binds in bulk_walk_cmd(
            _engine(),
            CommunityData(community, mpModel=1),
            await _target(ip),
            ContextData(),
            0,
            10,
            ObjectType(ObjectIdentity(base_oid)),
            lexicographicMode=False,
        ):
            if error_indication or error_status:
                break
            for oid, value in var_binds:
                oid_str = str(oid)
                if not oid_str.startswith(base_oid + "."):
                    return results
                results[oid_str[len(base_oid) + 1 :]] = value
    except Exception:
        logger.debug("SNMP raw walk failed for %s (%s)", ip, base_oid, exc_info=True)
    return results


async def walk_interfaces(ip: str, community: str) -> list[dict]:
    """Walk ifTable/ifXTable and return per-port stats. Ports missing from
    ifXTable (older/cheaper gear) are skipped rather than guessed at."""
    descr, oper_status, name, high_speed, in_octets, out_octets = await asyncio.gather(
        _bulk_walk(ip, community, OID_IF_DESCR),
        _bulk_walk(ip, community, OID_IF_OPER_STATUS),
        _bulk_walk(ip, community, OID_IF_NAME),
        _bulk_walk(ip, community, OID_IF_HIGH_SPEED),
        _bulk_walk(ip, community, OID_IF_HC_IN_OCTETS),
        _bulk_walk(ip, community, OID_IF_HC_OUT_OCTETS),
    )

    ports = []
    for if_index in descr:
        try:
            speed_mbps = int(high_speed.get(if_index, 0))
        except ValueError:
            speed_mbps = 0
        ports.append(
            {
                "if_index": int(if_index),
                "name": name.get(if_index) or descr.get(if_index, f"if{if_index}"),
                "status": "up" if oper_status.get(if_index) == str(OPER_STATUS_UP) else "down",
                "speed_mbps": speed_mbps,
                "in_octets": int(in_octets[if_index]) if if_index in in_octets else None,
                "out_octets": int(out_octets[if_index]) if if_index in out_octets else None,
            }
        )
    return ports
