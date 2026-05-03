"""
API FastAPI — Sistema VIGÍA OSINT/SOCMINT Monitor — VERSIÓN MILITAR
Endpoints para el dashboard de analistas con autenticación JWT, RBAC y auditoría completa.
"""
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Path, Query, Request, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from jose import JWTError

from src.database import (
    AlertModel, AuditLogModel, AnalystModel, ThreatIntelFeed,
    SystemMetricsModel, get_db, init_db, close_db,
)
from src.auth import (
    TokenData, AnalystCreate, AnalystLogin, TokenResponse,
    create_access_token, create_refresh_token, decode_token,
    hash_password, verify_password, verify_mfa_token,
    get_current_analyst, require_clearance, require_role,
    generate_hmac, verify_hmac,
)
from src.crypto_utils import encrypt_data, decrypt_data, encrypt_sensitive_field, decrypt_sensitive_field, hash_identifier
from src.cache import get_redis, close_redis, check_rate_limit, cache_get, cache_set
from src.models import (
    AlertLevel, AlertStatus, AlertResponse, AlertsResponse,
    AuditEntry, AuditLogResponse, SystemStats, ReviewRequest, ReviewResponse,
    OrchestratorResponse, AnalystReport, ThreatIndicator,
)
from sqlalchemy import select, update, delete, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Lifespan (startup/shutdown)
# ─────────────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Eventos de inicio y cierre de la aplicación."""
    logger.info("Sistema VIGÍA iniciando...")
    await init_db()
    logger.info("Base de datos inicializada")
    yield
    logger.info("Sistema VIGÍA apagando...")
    await close_db()
    await close_redis()
    logger.info("Recursos liberados")

# ─────────────────────────────────────────────────────────────────────────────
# App FastAPI
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="VIGÍA — Sistema OSINT/SOCMINT Monitor (MILITAR)",
    description="API para análisis pasivo de amenazas en contenido público de redes sociales. Nivel: ESTATAL-MILITAR",
    version="2.0.0",
    lifespan=lifespan,
    docs_url=None if os.environ.get("VIGIA_ENV") == "production" else "/docs",
    redoc_url=None,
)

# CORS: origenes explícitos desde variable de entorno
_raw_origins = os.environ.get("VIGIA_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)

# Security
security = HTTPBearer(auto_error=False)


# ─────────────────────────────────────────────────────────────────────────────
# Middleware de seguridad
# ─────────────────────────────────────────────────────────────────────────────
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Inyecta headers de seguridad HTTP en todas las respuestas."""
    # Rate limiting por IP
    client_ip = request.client.host if request.client else "unknown"
    allowed, rate_info = await check_rate_limit(client_ip, max_requests=100, window_seconds=60)

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=(), clipboard=()"

    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"detail": "Demasiadas peticiones"},
            headers={"Retry-After": str(rate_info["reset"])},
        )

    # Añadir headers de rate limit
    response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
    response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler global de excepciones."""
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    logger.error("ERROR no controlado en %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del sistema. Contacta al administrador."},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints de Autenticación
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/auth/login", response_model=TokenResponse)
async def login(credentials: AnalystLogin, request: Request, db: AsyncSession = Depends(get_db)):
    """Autenticación de analista con JWT + MFA opcional."""
    # Buscar analista por username
    result = await db.execute(
        select(AnalystModel).where(AnalystModel.username == credentials.username)
    )
    analyst = result.scalar_one_or_none()

    if not analyst or not verify_password(credentials.password, analyst.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # Verificar si la cuenta está bloqueada
    if analyst.locked_until and analyst.locked_until > datetime.now(timezone.utc):
        raise HTTPException(status_code=403, detail="Cuenta bloqueada. Intenta más tarde.")

    # Verificar MFA si está habilitado
    if analyst.mfa_enabled:
        if not credentials.mfa_token or not verify_mfa_token(analyst.mfa_secret or "", credentials.mfa_token):
            raise HTTPException(status_code=401, detail="Token MFA requerido o inválido")

    # Generar tokens
    token_data = {
        "sub": analyst.username,
        "role": analyst.role,
        "clearance": analyst.clearance_level,
        "analyst_id": analyst.id,
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Actualizar último login
    analyst.last_login = datetime.now(timezone.utc)
    analyst.failed_login_attempts = 0
    await db.commit()

    # Log de auditoría
    await _add_audit_entry(
        db=db,
        analyst_id=analyst.id,
        agent="AUTH",
        action_type="login_success",
        details=f"username={analyst.username} ip={request.client.host if request.client else 'unknown'}",
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=15 * 60,  # 15 minutos
    )


@app.post("/api/auth/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """Refresca el access token usando el refresh token."""
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token inválido")
        # Generar nuevo access token
        new_access = create_access_token({
            "sub": payload.sub,
            "role": payload.role,
            "clearance": payload.clearance,
            "analyst_id": payload.analyst_id,
        })
        return TokenResponse(
            access_token=new_access,
            refresh_token=refresh_token,
            expires_in=15 * 60,
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token inválido")


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints de Analistas (Solo Admin)
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/analysts", status_code=status.HTTP_201_CREATED)
async def create_analyst(
    data: AnalystCreate,
    db: AsyncSession = Depends(get_db),
    current: TokenData = Depends(get_current_analyst),
):
    """Crea un nuevo analista (solo admin)."""
    # Verificar que el usuario actual es admin
    if current.role != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden crear analistas")

    # Verificar si el username ya existe
    result = await db.execute(
        select(AnalystModel).where(AnalystModel.username == data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="El username ya existe")

    new_analyst = AnalystModel(
        username=data.username,
        email=data.email,
        full_name=data.full_name,
        password_hash=hash_password(data.password),
        role=data.role,
        clearance_level=data.clearance_level,
    )
    db.add(new_analyst)
    await db.commit()

    return {"message": "Analista creado", "analyst_id": new_analyst.id}


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints de Alertas (Requieren autenticación)
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/health", response_model=SystemStats)
async def health(db: AsyncSession = Depends(get_db)):
    """Estado del sistema y estadísticas generales."""
    # Obtener estadísticas de la base de datos
    result = await db.execute(
        select(
            func.count(AlertModel.id).label("total"),
            func.sum(func.case((AlertModel.status == AlertStatus.PENDIENTE, 1), else_=0)).label("pending"),
        )
    )
    stats = result.one()

    by_level_result = await db.execute(
        select(AlertModel.risk_level, func.count(AlertModel.id))
        .group_by(AlertModel.risk_level)
    )
    by_level = {level: count for level, count in by_level_result.all()}

    return SystemStats(
        alerts_today=stats.total or 0,
        pending_review=stats.pending or 0,
        by_level=by_level,
        system_status="online",
    )


@app.get("/api/alerts", response_model=AlertsResponse)
async def list_alerts(
    risk_level: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current: TokenData = Depends(get_current_analyst),
):
    """Lista de alertas con filtros opcionales."""
    query = select(AlertModel)

    # Aplicar filtros
    if risk_level:
        query = query.where(AlertModel.risk_level == risk_level)
    if platform:
        query = query.where(AlertModel.platform.ilike(platform))
    if status:
        query = query.where(AlertModel.status == status)

    # Ordenar por risk_score descendente
    query = query.order_by(desc(AlertModel.risk_score))

    # Contar total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Paginación
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    results = (await db.execute(query)).scalars().all()

    items = []
    for alert in results:
        indicators = json.loads(alert.indicators) if alert.indicators else []
        items.append({
            "id": alert.id,
            "platform": alert.platform,
            "content_excerpt": alert.content_excerpt,
            "indicators": indicators,
            "risk_score": alert.risk_score,
            "risk_level": alert.risk_level,
            "status": alert.status,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
        })

    return AlertsResponse(items=items, total=total, page=page, page_size=page_size)


@app.get("/api/alerts/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str = Path(..., max_length=128),
    db: AsyncSession = Depends(get_db),
    current: TokenData = Depends(get_current_analyst),
):
    """Detalle completo de una alerta (descifra contenido)."""
    result = await db.execute(select(AlertModel).where(AlertModel.id == alert_id))
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")

    # Descifrar contenido sensible
    content_full = decrypt_sensitive_field(alert.content_full_encrypted) or alert.content_excerpt
    analyst_notes = decrypt_sensitive_field(alert.analyst_notes) if alert.analyst_notes else None

    indicators = json.loads(alert.indicators) if alert.indicators else []

    return AlertResponse(
        id=alert.id,
        platform=alert.platform,
        content_excerpt=alert.content_excerpt,
        content_full=content_full,
        indicators=indicators,
        risk_score=alert.risk_score,
        risk_level=alert.risk_level,
        status=alert.status,
        created_at=alert.created_at.isoformat() if alert.created_at else None,
        reviewed_at=alert.reviewed_at.isoformat() if alert.reviewed_at else None,
        reviewed_by=alert.reviewed_by,
        analyst_notes=analyst_notes,
    )


@app.post("/api/alerts/{alert_id}/review", response_model=ReviewResponse)
async def review_alert(
    request: Request,
    body: ReviewRequest,
    alert_id: str = Path(..., max_length=128),
    db: AsyncSession = Depends(get_db),
    current: TokenData = Depends(get_current_analyst),
):
    """Registra la decisión del analista sobre una alerta."""
    result = await db.execute(select(AlertModel).where(AlertModel.id == alert_id))
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")

    if alert.status != AlertStatus.PENDIENTE:
        raise HTTPException(status_code=409, detail="La alerta ya fue revisada")

    # Mapear acción a status
    status_map = {
        "ESCALAR": AlertStatus.ESCALADA,
        "ARCHIVAR": AlertStatus.ARCHIVADA,
        "FALSO_POSITIVO": AlertStatus.FALSO_POSITIVO,
    }
    new_status = status_map.get(body.action, AlertStatus.ARCHIVADA)

    # Cifrar notas del analista
    notes_encrypted = encrypt_sensitive_field(body.notes) if body.notes else None

    alert.status = new_status
    alert.reviewed_at = datetime.now(timezone.utc)
    alert.reviewed_by = current.analyst_id
    alert.analyst_notes = notes_encrypted

    await db.commit()

    # Log de auditoría
    await _add_audit_entry(
        db=db,
        analyst_id=current.analyst_id,
        agent="ANALYST",
        action_type=f"review_{body.action.lower()}",
        details=f"analista={current.username} accion={body.action} alert_id={alert_id}",
        alert_id=alert_id,
        ip_address=request.client.host if request.client else None,
    )

    return ReviewResponse(
        success=True,
        message=f"Decisión registrada: {body.action} — {new_status}",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints de Auditoría
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/audit-log", response_model=AuditLogResponse)
async def get_audit_log(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    agent: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current: TokenData = Depends(get_current_analyst),
):
    """Log de auditoría con filtros (solo supervisores+)."""
    # Verificar nivel de acceso
    if current.role not in ["supervisor", "admin"]:
        raise HTTPException(status_code=403, detail="Requiere nivel de supervisor")

    query = select(AuditLogModel)

    if agent:
        query = query.where(AuditLogModel.agent.ilike(f"%{agent}%"))
    if action_type:
        query = query.where(AuditLogModel.action_type.ilike(f"%{action_type}%"))
    if date_from:
        query = query.where(AuditLogModel.timestamp >= date_from)
    if date_to:
        query = query.where(AuditLogModel.timestamp <= date_to)

    query = query.order_by(desc(AuditLogModel.timestamp))

    # Contar total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Paginación
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    results = (await db.execute(query)).scalars().all()

    items = [
        AuditEntry(
            id=entry.id,
            timestamp=entry.timestamp.isoformat() if entry.timestamp else None,
            agent=entry.agent,
            action_type=entry.action_type,
            target_id=entry.target_id,
            details=entry.details,
            alert_id=entry.alert_id,
        )
        for entry in results
    ]

    return AuditLogResponse(items=items, total=total, page=page, page_size=page_size)


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints de Análisis (Orquestador)
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/analyze", response_model=OrchestratorResponse)
async def run_analysis(
    objective: str = Query(..., min_length=5, max_length=500),
    platforms: Optional[str] = Query(None),
    max_results: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current: TokenData = Depends(get_current_analyst),
):
    """Lanza un ciclo completo de análisis OSINT/SOCMINT."""
    from src.orchestrator import VigiaOrchestrator

    # Verificar nivel de habilitación
    if current.clearance not in ["SECRET", "TOP_SECRET"]:
        raise HTTPException(status_code=403, detail="Requiere nivel de habilitación SECRET+")

    platform_list = None
    if platforms:
        platform_list = [p.strip().lower() for p in platforms.split(",") if p.strip()]

    orchestrator = VigiaOrchestrator()
    result = await orchestrator.run_analysis_pipeline(
        objective=objective,
        platforms=platform_list,
        max_results=max_results,
        db=db,
        analyst_id=current.analyst_id,
    )

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Función auxiliar para auditoría
# ─────────────────────────────────────────────────────────────────────────────
async def _add_audit_entry(
    db: AsyncSession,
    agent: str,
    action_type: str,
    details: str,
    analyst_id: str | None = None,
    alert_id: str | None = None,
    target_id: str | None = None,
    ip_address: str | None = None,
):
    """Añade una entrada al log de auditoría con HMAC."""
    entry_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc)

    # Generar HMAC para integridad
    hmac_data = f"{entry_id}{timestamp}{agent}{action_type}{details}"
    hmac_signature = generate_hmac(hmac_data)

    entry = AuditLogModel(
        id=entry_id,
        timestamp=timestamp,
        session_id=None,  # Asociar con sesión si está disponible
        agent=agent,
        action_type=action_type,
        target_id=target_id,
        alert_id=alert_id,
        details=details,
        ip_address=ip_address,
        analyst_id=analyst_id,
        hmac_signature=hmac_signature,
    )
    db.add(entry)
    await db.commit()
    logger.info("[AUDIT] %s | %s | %s", agent, action_type, details)
