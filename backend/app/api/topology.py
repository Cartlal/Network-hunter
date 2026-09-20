from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Device, Link
from app.schemas import TopologyOut
from app.ws.manager import manager

router = APIRouter()


@router.get("/api/topology", response_model=TopologyOut)
async def get_topology(session: AsyncSession = Depends(get_session)) -> TopologyOut:
    devices = (await session.execute(select(Device))).scalars().all()
    links = (await session.execute(select(Link))).scalars().all()
    return TopologyOut(devices=devices, links=links)


@router.websocket("/ws/topology")
async def topology_ws(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            # Client doesn't need to send anything; keep the connection open
            # and drop it cleanly if the browser closes the socket.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
