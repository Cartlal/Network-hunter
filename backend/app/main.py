import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

if sys.platform == "win32":
    # Discovery relies on asyncio.create_subprocess_exec (ipconfig, arp -a),
    # which only works under the Proactor loop on Windows. uvicorn's
    # --reload supervisor can otherwise leave the Selector loop active,
    # breaking every subprocess call with a NotImplementedError.
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from app.alerts.rules import alert_evaluation_loop
from app.api.activity import router as activity_router
from app.api.alerts import router as alerts_router
from app.api.devices import router as devices_router
from app.api.history import router as history_router
from app.api.ports import router as ports_router
from app.api.security import router as security_router
from app.api.speedtest import router as speedtest_router
from app.api.topology import router as topology_router
from app.db import init_db
from app.discovery.lldp_cdp import reconcile_links_loop
from app.discovery.scheduler import scan_loop
from app.discovery.snmp_poll import snmp_poll_loop, snmp_probe_loop
from app.security.engine import security_scan_loop

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    tasks = [
        asyncio.create_task(scan_loop()),
        asyncio.create_task(snmp_probe_loop()),
        asyncio.create_task(snmp_poll_loop()),
        asyncio.create_task(reconcile_links_loop()),
        asyncio.create_task(alert_evaluation_loop()),
        asyncio.create_task(security_scan_loop()),
    ]
    try:
        yield
    finally:
        for task in tasks:
            task.cancel()


app = FastAPI(title="Network Hunter API", lifespan=lifespan)

cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(topology_router)
app.include_router(devices_router)
app.include_router(history_router)
app.include_router(alerts_router)
app.include_router(activity_router)
app.include_router(ports_router)
app.include_router(security_router)
app.include_router(speedtest_router)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


# Production convenience: if the frontend has been built (`npm run build`),
# serve it directly from the backend so the whole app is one process on one
# port. In dev, run the Vite dev server separately instead (see SETUP.md).
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
