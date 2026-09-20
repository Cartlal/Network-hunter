import asyncio
import datetime
import logging

import speedtest

from app.db import SessionLocal
from app.models import SpeedTestResult

logger = logging.getLogger("netmap.speedtest")


def _run_sync() -> dict:
    """Blocking WAN speed test via speedtest.net's public infrastructure -
    run off the event loop thread (see run_speed_test). Raises on failure
    (no internet, speedtest.net unreachable, etc.); the caller turns that
    into a clean 502 rather than a silent/misleading result."""
    client = speedtest.Speedtest(secure=True)
    client.get_best_server()
    download_bps = client.download()
    upload_bps = client.upload()
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
