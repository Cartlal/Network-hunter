from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_session
from app.models import Device, Port
from app.schemas import DeviceNameIn, DeviceOut, DevicePositionIn, MapPositionIn, PortOut, SnmpConfigIn

router = APIRouter()


@router.get("/api/devices", response_model=list[DeviceOut])
async def list_devices(session: AsyncSession = Depends(get_session)) -> list[Device]:
    return (await session.execute(select(Device))).scalars().all()


@router.get("/api/devices/{device_id}", response_model=DeviceOut)
async def get_device(device_id: int, session: AsyncSession = Depends(get_session)) -> Device:
    device = await session.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.get("/api/devices/{device_id}/ports", response_model=list[PortOut])
async def get_device_ports(device_id: int, session: AsyncSession = Depends(get_session)) -> list[Port]:
    device = await session.get(Device, device_id, options=[selectinload(Device.ports)])
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return device.ports


@router.put("/api/devices/{device_id}/snmp-config", response_model=DeviceOut)
async def set_snmp_config(
    device_id: int,
    config: SnmpConfigIn,
    session: AsyncSession = Depends(get_session),
) -> Device:
    device = await session.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    device.snmp_enabled = config.snmp_enabled
    if config.snmp_community:
        device.snmp_community = config.snmp_community
    if not config.snmp_enabled:
        device.snmp_supported = None  # allow auto re-probe if re-enabled later
    await session.commit()
    await session.refresh(device)
    return device


@router.put("/api/devices/{device_id}/name", response_model=DeviceOut)
async def set_device_name(
    device_id: int,
    payload: DeviceNameIn,
    session: AsyncSession = Depends(get_session),
) -> Device:
    device = await session.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    device.custom_name = payload.custom_name.strip() if payload.custom_name else None
    await session.commit()
    await session.refresh(device)
    return device


@router.put("/api/devices/{device_id}/position", response_model=DeviceOut)
async def set_device_position(
    device_id: int,
    position: DevicePositionIn,
    session: AsyncSession = Depends(get_session),
) -> Device:
    device = await session.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    device.pos_x = position.pos_x
    device.pos_y = position.pos_y
    await session.commit()
    await session.refresh(device)
    return device


@router.put("/api/devices/{device_id}/map-position", response_model=DeviceOut)
async def set_device_map_position(
    device_id: int,
    position: MapPositionIn,
    session: AsyncSession = Depends(get_session),
) -> Device:
    device = await session.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    device.map_x = position.map_x
    device.map_y = position.map_y
    await session.commit()
    await session.refresh(device)
    return device
