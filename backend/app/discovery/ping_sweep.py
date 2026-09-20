import asyncio
import ipaddress
import socket

from icmplib import async_ping

COMMON_TCP_PORTS = (80, 443, 22, 445, 139, 135, 8080)
CONCURRENCY = 64


def get_local_ip() -> str:
    """The host's own LAN-facing IP, found by opening a UDP socket to a
    public IP (no packets are actually sent for UDP connect)."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]


def get_local_network() -> ipaddress.IPv4Network:
    """Best-effort guess of the host's local /24."""
    return ipaddress.ip_network(f"{get_local_ip()}/24", strict=False)


async def _tcp_probe(ip: str, ports: tuple[int, ...] = COMMON_TCP_PORTS, timeout: float = 0.5) -> bool:
    for port in ports:
        try:
            fut = asyncio.open_connection(ip, port)
            reader, writer = await asyncio.wait_for(fut, timeout=timeout)
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            continue
    return False


async def _probe_host(ip: str, semaphore: asyncio.Semaphore) -> tuple[str, float | None] | None:
    """Returns (ip, latency_ms) if reachable, None otherwise. latency_ms is
    None when the host only answered a TCP probe (no RTT measurement)."""
    async with semaphore:
        try:
            result = await async_ping(ip, count=1, timeout=0.6, privileged=False)
            if result.is_alive:
                return ip, result.avg_rtt
        except Exception:
            pass
        if await _tcp_probe(ip):
            return ip, None
        return None


async def sweep_subnet(network: ipaddress.IPv4Network | None = None) -> dict[str, float | None]:
    """Sweep every host in the local /24, return {ip: latency_ms} for hosts
    that responded to ICMP or a common TCP port. Populates the OS ARP cache
    as a side effect."""
    network = network or get_local_network()
    semaphore = asyncio.Semaphore(CONCURRENCY)
    hosts = [str(h) for h in network.hosts()]
    results = await asyncio.gather(*(_probe_host(ip, semaphore) for ip in hosts))
    return dict(r for r in results if r)
