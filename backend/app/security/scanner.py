import asyncio

from app.security.catalog import RISKY_SERVICES, RiskyService

CONNECT_TIMEOUT_SECONDS = 0.6
BANNER_READ_TIMEOUT_SECONDS = 0.4
BANNER_MAX_BYTES = 200
CONCURRENCY = 32


async def _probe_service(ip: str, service: RiskyService) -> dict | None:
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, service.port), timeout=CONNECT_TIMEOUT_SECONDS
        )
    except Exception:
        return None

    banner: str | None = None
    try:
        # Many of these services (FTP, Telnet, SMTP-likes) print a banner
        # unsolicited on connect. A timeout/empty read just means no banner -
        # not every service does this (RDP/VNC/SMB need a handshake first),
        # and that's fine - the finding still stands without one.
        raw = await asyncio.wait_for(reader.read(BANNER_MAX_BYTES), timeout=BANNER_READ_TIMEOUT_SECONDS)
        if raw:
            first_line = raw.decode(errors="ignore").strip().splitlines()[0]
            banner = first_line[:200] or None
    except Exception:
        pass
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass

    return {"service": service, "banner": banner}


async def scan_device(ip: str) -> list[dict]:
    """Probe every catalogued risky port with a plain, unprivileged TCP
    connect (same technique as discovery/ping_sweep.py's _tcp_probe) and
    return the ones that answered, each with a best-effort banner."""
    semaphore = asyncio.Semaphore(CONCURRENCY)

    async def _bounded(service: RiskyService) -> dict | None:
        async with semaphore:
            return await _probe_service(ip, service)

    results = await asyncio.gather(*(_bounded(service) for service in RISKY_SERVICES))
    return [r for r in results if r]
