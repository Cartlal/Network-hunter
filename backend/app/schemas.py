import datetime

from pydantic import BaseModel, ConfigDict


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ip: str
    mac: str | None
    hostname: str | None
    custom_name: str | None
    vendor: str | None
    device_type_guess: str
    is_gateway: bool
    status: str
    first_seen: datetime.datetime
    last_seen: datetime.datetime
    model: str | None
    firmware: str | None
    uptime_seconds: float | None
    snmp_enabled: bool
    snmp_supported: bool | None
    pos_x: float | None
    pos_y: float | None
    map_x: float | None
    map_y: float | None
    security_score: int


class LinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    from_device_id: int
    to_device_id: int
    inferred: bool
    speed_mbps: int | None
    duplex: str | None


class TopologyOut(BaseModel):
    devices: list[DeviceOut]
    links: list[LinkOut]


class DeviceStatusUpdate(BaseModel):
    id: int
    status: str
    last_seen: datetime.datetime


class PortOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    if_index: int
    name: str
    status: str
    speed_mbps: int
    duplex: str | None
    rx_bps: float
    tx_bps: float


class SnmpConfigIn(BaseModel):
    snmp_enabled: bool
    snmp_community: str | None = None


class DevicePositionIn(BaseModel):
    pos_x: float
    pos_y: float


class MapPositionIn(BaseModel):
    map_x: float
    map_y: float


class DeviceNameIn(BaseModel):
    custom_name: str | None = None


class MetricSampleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ts: datetime.datetime
    value: float


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    rule_type: str
    severity: str
    message: str
    created_at: datetime.datetime
    resolved_at: datetime.datetime | None


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int | None
    event_type: str
    message: str
    created_at: datetime.datetime


class SecurityFindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    finding_type: str
    port: int | None
    service_name: str
    banner: str | None
    severity: str
    title: str
    detail: str
    remediation: str
    first_seen: datetime.datetime
    last_seen: datetime.datetime
    resolved_at: datetime.datetime | None
    acknowledged_at: datetime.datetime | None


class SecurityOverviewOut(BaseModel):
    network_score: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    devices_scanned: int
    last_scan_at: datetime.datetime | None
