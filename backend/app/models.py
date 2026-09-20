import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    ip: Mapped[str] = mapped_column(String, unique=True, index=True)
    mac: Mapped[str | None] = mapped_column(String, nullable=True)
    hostname: Mapped[str | None] = mapped_column(String, nullable=True)
    # User-assigned label - takes priority over the auto-discovered hostname
    # everywhere in the UI. Auto-discovery (DNS/mDNS) never reaches 100% of
    # devices - some gear (managed switches in controller mode, appliances)
    # just doesn't announce a name over any protocol we can query.
    custom_name: Mapped[str | None] = mapped_column(String, nullable=True)
    vendor: Mapped[str | None] = mapped_column(String, nullable=True)
    device_type_guess: Mapped[str] = mapped_column(String, default="unknown")
    is_gateway: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String, default="offline")
    first_seen: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
    last_seen: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )

    # Phase 2: SNMP enrichment - most consumer devices never populate these.
    model: Mapped[str | None] = mapped_column(String, nullable=True)
    firmware: Mapped[str | None] = mapped_column(String, nullable=True)
    uptime_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    snmp_community: Mapped[str | None] = mapped_column(String, nullable=True)
    snmp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    snmp_supported: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Phase 3: manual layout position, persisted once the user drags a node.
    pos_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    pos_y: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Physical/site map placement - independent of the logical topology layout.
    map_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    map_y: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Security posture: 0-100, recomputed by the security scanner every pass
    # from this device's active, unacknowledged findings (see app/security/).
    security_score: Mapped[int] = mapped_column(Integer, default=100)

    ports: Mapped[list["Port"]] = relationship(back_populates="device", cascade="all, delete-orphan")


class Port(Base):
    __tablename__ = "ports"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"))
    if_index: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="unknown")
    speed_mbps: Mapped[int] = mapped_column(Integer, default=0)
    duplex: Mapped[str | None] = mapped_column(String, nullable=True)
    rx_bps: Mapped[float] = mapped_column(Float, default=0)
    tx_bps: Mapped[float] = mapped_column(Float, default=0)
    _last_in_octets: Mapped[int | None] = mapped_column("last_in_octets", Integer, nullable=True)
    _last_out_octets: Mapped[int | None] = mapped_column("last_out_octets", Integer, nullable=True)
    _last_sample_at: Mapped[datetime.datetime | None] = mapped_column(
        "last_sample_at", DateTime, nullable=True
    )

    device: Mapped["Device"] = relationship(back_populates="ports")


class Link(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(primary_key=True)
    from_device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"))
    to_device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"))
    inferred: Mapped[bool] = mapped_column(Boolean, default=True)
    speed_mbps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duplex: Mapped[str | None] = mapped_column(String, nullable=True)

    from_device: Mapped["Device"] = relationship(foreign_keys=[from_device_id])
    to_device: Mapped["Device"] = relationship(foreign_keys=[to_device_id])


class MetricSample(Base):
    """A single time-series data point. On Postgres this table is converted
    to a TimescaleDB hypertable (see db.py); on SQLite it's a plain indexed
    table, which is fine at single-LAN scale but won't downsample/retain."""

    __tablename__ = "metric_samples"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    metric_type: Mapped[str] = mapped_column(String, index=True)  # latency_ms | rx_bps | tx_bps
    ts: Mapped[datetime.datetime] = mapped_column(DateTime, index=True, default=datetime.datetime.utcnow)
    value: Mapped[float] = mapped_column(Float)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"))
    rule_type: Mapped[str] = mapped_column(String)  # device_down | high_bandwidth | high_latency
    severity: Mapped[str] = mapped_column(String, default="warning")  # warning | critical
    message: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    resolved_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)

    device: Mapped["Device"] = relationship()


class ActivityLog(Base):
    __tablename__ = "activity_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int | None] = mapped_column(ForeignKey("devices.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String)  # connected | disconnected | alert | firmware_updated
    message: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, index=True)


class SecurityFinding(Base):
    """A single security-posture finding for a device: an exposed legacy/
    high-risk service, or SNMP answering on a well-known default community
    string. Produced by app/security/engine.py, re-evaluated every scan pass
    so a finding that stops reproducing gets resolved automatically."""

    __tablename__ = "security_findings"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    finding_type: Mapped[str] = mapped_column(String)  # insecure_service | weak_snmp_credential
    port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    service_name: Mapped[str] = mapped_column(String)
    banner: Mapped[str | None] = mapped_column(String, nullable=True)
    severity: Mapped[str] = mapped_column(String)  # low | medium | high | critical
    title: Mapped[str] = mapped_column(String)
    detail: Mapped[str] = mapped_column(String)
    remediation: Mapped[str] = mapped_column(String)
    first_seen: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    last_seen: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    resolved_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    acknowledged_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)

    device: Mapped["Device"] = relationship()
