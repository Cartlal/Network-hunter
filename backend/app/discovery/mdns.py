import asyncio
import logging
import socket
import struct
import time

logger = logging.getLogger("netmap.mdns")

MDNS_ADDR = "224.0.0.251"
MDNS_PORT = 5353
QUERY_WINDOW_SECONDS = 3.0

PTR_TYPE = 12
A_TYPE = 1


def _parse_name(data: bytes, offset: int) -> tuple[str, int]:
    """Parse a (possibly compressed) DNS name starting at offset. Returns the
    dotted name and the offset immediately after it in the original packet."""
    labels = []
    original_offset = offset
    jumped = False
    for _ in range(128):  # hard cap - malformed/hostile packets shouldn't loop forever
        length = data[offset]
        if length == 0:
            offset += 1
            break
        if length & 0xC0 == 0xC0:
            pointer = ((length & 0x3F) << 8) | data[offset + 1]
            if not jumped:
                original_offset = offset + 2
            offset = pointer
            jumped = True
            continue
        offset += 1
        labels.append(data[offset : offset + length].decode(errors="replace"))
        offset += length
    return ".".join(labels), (original_offset if jumped else offset)


def _build_ptr_query(ip: str) -> bytes:
    reversed_octets = ".".join(reversed(ip.split(".")))
    qname = reversed_octets + ".in-addr.arpa"
    header = struct.pack(">HHHHHH", 0, 0, 1, 0, 0, 0)
    encoded = b"".join(bytes([len(part)]) + part.encode() for part in qname.split(".")) + b"\x00"
    return header + encoded + struct.pack(">HH", PTR_TYPE, 0x0001)


def _reverse_arpa_to_ip(name: str) -> str | None:
    if not name.endswith(".in-addr.arpa"):
        return None
    octets = name[: -len(".in-addr.arpa")].split(".")
    if len(octets) != 4:
        return None
    return ".".join(reversed(octets))


def _query_sync(ips: list[str], local_ip: str) -> dict[str, str]:
    """Blocking implementation - send PTR queries for each IP on the actual
    LAN interface (binding matters: on a multi-homed host, joining the
    multicast group on the wrong adapter silently receives nothing) and
    collect any PTR/A responses within the query window."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("", MDNS_PORT))
    except OSError:
        # Port already bound by another mDNS responder on this host - fall
        # back to an ephemeral port; we can still send queries and receive
        # unicast-ish replies routed back to us via the socket.
        sock.bind(("", 0))
    mreq = struct.pack("4s4s", socket.inet_aton(MDNS_ADDR), socket.inet_aton(local_ip))
    try:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    except OSError:
        logger.debug("Could not join mDNS multicast group on %s", local_ip, exc_info=True)
        sock.close()
        return {}
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(local_ip))
    sock.settimeout(0.5)

    for ip in ips:
        try:
            sock.sendto(_build_ptr_query(ip), (MDNS_ADDR, MDNS_PORT))
        except OSError:
            pass

    found: dict[str, str] = {}
    end = time.monotonic() + QUERY_WINDOW_SECONDS
    while time.monotonic() < end:
        try:
            data, _ = sock.recvfrom(8192)
        except TimeoutError:
            continue
        except OSError:
            break
        try:
            qdcount, ancount = struct.unpack(">HH", data[4:8])
            offset = 12
            for _ in range(qdcount):
                _, offset = _parse_name(data, offset)
                offset += 4
            for _ in range(ancount):
                name, offset = _parse_name(data, offset)
                rtype, _rclass, _ttl, rdlength = struct.unpack(">HHIH", data[offset : offset + 10])
                offset += 10
                if rtype == PTR_TYPE:
                    target_ip = _reverse_arpa_to_ip(name)
                    ptr_name, _ = _parse_name(data, offset)
                    if target_ip and ptr_name.endswith(".local"):
                        found[target_ip] = ptr_name[: -len(".local")]
                offset += rdlength
        except (struct.error, IndexError):
            continue

    sock.close()
    return found


async def mdns_reverse_lookup(ips: list[str], local_ip: str) -> dict[str, str]:
    """Best-effort hostname discovery for devices that don't have reverse-DNS
    PTR records (most phones/tablets/IoT) but do speak mDNS - which is most
    modern consumer devices. Returns {ip: name} for whatever responded."""
    if not ips:
        return {}
    try:
        return await asyncio.to_thread(_query_sync, ips, local_ip)
    except Exception:
        logger.debug("mDNS reverse lookup failed", exc_info=True)
        return {}
