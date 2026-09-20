from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Port
from app.schemas import PortOut

router = APIRouter()


@router.get("/api/ports", response_model=list[PortOut])
async def list_all_ports(session: AsyncSession = Depends(get_session)) -> list[Port]:
    return (await session.execute(select(Port))).scalars().all()
