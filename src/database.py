"""
Configuración de base de datos PostgreSQL con SQLAlchemy (async).
Soporte para cifrado en reposo y auditoría.
"""
import os
from typing import AsyncGenerator

from sqlalchemy import Column, DateTime, String, Text, Integer, Boolean, Float, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime
import uuid


# ─────────────────────────────────────────────────────────────────────────────
# Configuración de motor de base de datos
# ─────────────────────────────────────────────────────────────────────────────
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://vigia:vigia_secure@localhost:5432/vigia_db"
)

# Para desarrollo con SQLite (opcional)
USE_SQLITE = os.environ.get("USE_SQLITE", "false").lower() == "true"
if USE_SQLITE:
    DATABASE_URL = "sqlite+aiosqlite:///./vigia.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ─────────────────────────────────────────────────────────────────────────────
# Base para modelos
# ─────────────────────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ─────────────────────────────────────────────────────────────────────────────
# Modelos de base de datos
# ─────────────────────────────────────────────────────────────────────────────

class AlertModel(Base):
    """Modelo de alerta persistido en PostgreSQL."""
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    content_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    content_full_encrypted: Mapped[str] = mapped_column(Text, nullable=False)  # Cifrado en reposo
    author_id_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Risk assessment
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    indicators: Mapped[str] = mapped_column(Text, nullable=False)  # JSON serializado

    # Estado
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDIENTE", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Auditoría
    analyst_notes_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)  # Cifrado
    model_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")
    session_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


class AuditLogModel(Base):
    """Log de auditoría inmutable."""
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    session_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    agent: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    alert_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    analyst_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hmac_signature: Mapped[str] = mapped_column(String(64), nullable=False)  # Integridad


class AnalystModel(Base):
    """Modelo de analistas con roles y habilitación."""
    __tablename__ = "analysts"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="analyst")  # analyst, supervisor, admin
    clearance_level: Mapped[str] = mapped_column(String(20), nullable=False, default="CONFIDENTIAL")  # CONFIDENTIAL, SECRET, TOP_SECRET
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mfa_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ThreatIntelFeed(Base):
    """Feeds de inteligencia de amenazas (STIX/TAXII)."""
    __tablename__ = "threat_intel_feeds"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    source: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    feed_type: Mapped[str] = mapped_column(String(64), nullable=False)  # ioc, ttp, actor
    indicator_value: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    indicator_type: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class SystemMetricsModel(Base):
    """Métricas del sistema para monitoreo."""
    __tablename__ = "system_metrics"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    metric_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON


# ─────────────────────────────────────────────────────────────────────────────
# Utilidades de sesión
# ─────────────────────────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Proveedor de sesión de base de datos."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Inicializa la base de datos creando todas las tablas."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Cierra la conexión a la base de datos."""
    await engine.dispose()
