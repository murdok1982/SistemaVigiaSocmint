"""
Configuración de base de datos PostgreSQL con SQLAlchemy (async).
Soporte para cifrado en reposo y auditoría.
"""
import os
import logging
from typing import AsyncGenerator

from sqlalchemy import Column, DateTime, String, Text, Integer, Boolean, Float, Enum as SQLEnum, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime, timezone
import uuid

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Configuración de motor de base de datos
# ─────────────────────────────────────────────────────────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL", None)
if DATABASE_URL is None:
    if os.environ.get("VIGIA_ENV", "development").lower() == "production":
        raise RuntimeError("DATABASE_URL no está definida. Es obligatoria en producción.")
    DATABASE_URL = "sqlite+aiosqlite:///./vigia.db"

# Para desarrollo con SQLite (opcional)
USE_SQLITE = os.environ.get("USE_SQLITE", "false").lower() == "true"
if USE_SQLITE:
    DATABASE_URL = "sqlite+aiosqlite:///./vigia.db"

_engine_kwargs: dict = {"echo": False}
if not USE_SQLITE:
    _engine_kwargs.update(
        pool_size=20,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
    )

engine = create_async_engine(DATABASE_URL, **_engine_kwargs)

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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
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
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    session_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    agent: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    alert_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    analyst_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hmac_signature: Mapped[str] = mapped_column(String(64), nullable=False)  # Integridad
    chain_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)


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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    failed_login_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    password_change_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class ThreatIntelFeed(Base):
    """Feeds de inteligencia de amenazas (STIX/TAXII)."""
    __tablename__ = "threat_intel_feeds"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    source: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    feed_type: Mapped[str] = mapped_column(String(64), nullable=False)  # ioc, ttp, actor
    indicator_value: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    indicator_type: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class SystemMetricsModel(Base):
    """Métricas del sistema para monitoreo."""
    __tablename__ = "system_metrics"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
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
    """
    Inicializa la base de datos.

    - En desarrollo (USE_SQLITE o VIGIA_ENV != 'production'): hace create_all
      como fallback, idempotente.
    - En producción: NO ejecuta create_all. Se asume que Alembic ya migró el
      esquema. Solo siembra el admin si falta.
    """
    vigia_env = os.environ.get("VIGIA_ENV", "development").lower()
    is_production = vigia_env == "production"

    if not is_production or USE_SQLITE:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    await _bootstrap_admin_if_missing()


async def _bootstrap_admin_if_missing() -> None:
    """
    Crea el admin inicial si no existe ningún usuario con role='admin'.
    Requiere VIGIA_ADMIN_BOOTSTRAP_PASSWORD; si no está, log de WARNING y aborta.
    El admin se crea con password_change_required=True.
    """
    from src.auth import hash_password  # import diferido para evitar ciclos

    bootstrap_username = os.environ.get("VIGIA_ADMIN_BOOTSTRAP_USERNAME", "admin")
    bootstrap_password = os.environ.get("VIGIA_ADMIN_BOOTSTRAP_PASSWORD")

    async with async_session() as session:
        result = await session.execute(
            select(AnalystModel).where(AnalystModel.role == "admin")
        )
        existing_admin = result.scalar_one_or_none()
        if existing_admin is not None:
            return

        if not bootstrap_password:
            logger.warning(
                "No existe ningún admin y VIGIA_ADMIN_BOOTSTRAP_PASSWORD no está "
                "definida. NO se crea admin con contraseña vacía."
            )
            return

        admin = AnalystModel(
            username=bootstrap_username,
            email=f"{bootstrap_username}@vigia.local",
            full_name="Administrador VIGIA",
            password_hash=hash_password(bootstrap_password),
            role="admin",
            clearance_level="TOP_SECRET",
            is_active=True,
            mfa_enabled=False,
            password_change_required=True,
        )
        session.add(admin)
        await session.commit()
        logger.info("Admin bootstrap creado: %s", bootstrap_username)


async def close_db() -> None:
    """Cierra la conexión a la base de datos."""
    await engine.dispose()
