import logging
import os
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger("netmap.db")

DB_PATH = Path(__file__).resolve().parent.parent / "netmap.db"
DEFAULT_DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

# Phases 1-3 run fine on the SQLite default. Set DATABASE_URL to a Postgres
# DSN (see docker-compose.yml) to get TimescaleDB-backed metric history for
# Phase 4 - `postgresql+asyncpg://user:pass@localhost:5432/netmap`.
DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def _init_timescale(conn) -> None:
    """Best-effort: convert metric_samples into a TimescaleDB hypertable.
    No-ops (with a log line) if the timescaledb extension isn't installed -
    the table still works as a plain Postgres table either way."""
    try:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))
        await conn.execute(
            text("SELECT create_hypertable('metric_samples', 'ts', if_not_exists => TRUE)")
        )
    except Exception:
        logger.warning("TimescaleDB extension unavailable - metric_samples stays a plain table", exc_info=True)


async def init_db() -> None:
    from app import models  # noqa: F401 - ensure models are registered

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if engine.dialect.name == "postgresql":
            await _init_timescale(conn)


async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
