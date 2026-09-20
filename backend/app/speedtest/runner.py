import asyncio
import datetime
import logging

import speedtest

from app.db import SessionLocal
from app.models import SpeedTestResult

logger = logging.getLogger("netmap.speedtest")

# speedtest-cli's own upload default (2 threads) badly undersaturates
# anything faster than a modest connection - a single-digit-Mbps gap is
# expected vs the official site/app, but 2 threads can leave a fast link
# reporting a fraction of its real upload capacity. Push both directions
# harder; download's config default is already a reasonable 8.
DOWNLOAD_THREADS = 8
UPLOAD_THREADS = 4


def _select_server(client: "speedtest.Speedtest") -> None:
    """Prefer a nearby server run by the user's own ISP when one is listed.
    A same-ISP path skips inter-provider peering and is usually the most
    representative of real achievable throughput - it's the same bias
    Ookla's own apps and website use, and pure lowest-latency selection can
    miss it if a geographically closer but unrelated server pings a hair
    faster."""
    isp = (client.config.get("client", {}).get("isp") or "").lower()
    candidates = client.get_closest_servers(limit=10)
    match = next((s for s in candidates if isp and isp in s.get("sponsor", "").lower()), None)
    client.get_best_server(servers=[match] if match else None)


def _run_sync() -> dict:
    """Blocking WAN speed test via speedtest.net's public infrastructure -
    run off the event loop thread (see run_speed_test). Raises on failure
    (no internet, speedtest.net unreachable, etc.); the caller turns that
    into a clean 502 rather than a silent/misleading result."""
    client = speedtest.Speedtest(secure=True)
    _select_server(client)
    download_bps = client.download(threads=DOWNLOAD_THREADS)
    upload_bps = client.upload(threads=UPLOAD_THREADS)
    results = client.results.dict()
    server = results.get("server", {})
    sponsor = server.get("sponsor", "Unknown")
    name = server.get("name", "")
    return {
        "download_mbps": download_bps / 1_000_000,
        "upload_mbps": upload_bps / 1_000_000,
        "ping_ms": results.get("ping", 0.0),
        "server_name": f"{sponsor} ({name})" if name else sponsor,
    }


async def run_speed_test() -> SpeedTestResult:
    data = await asyncio.to_thread(_run_sync)
    now = datetime.datetime.utcnow()
    async with SessionLocal() as session:
        result = SpeedTestResult(
            download_mbps=data["download_mbps"],
            upload_mbps=data["upload_mbps"],
            ping_ms=data["ping_ms"],
            server_name=data["server_name"],
            tested_at=now,
        )
        session.add(result)
        await session.commit()
        await session.refresh(result)
        return result
