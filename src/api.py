"""
API FastAPI — Sistema VIGÍA OSINT/SOCMINT Monitor — VERSIÓN MILITAR
Endpoints para el dashboard de analistas con autenticación JWT, RBAC y auditoría completa.
"""
import logging
import os
import time
import hispan_shield_guardian
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Path, Query, Request, Security, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, PlainTextResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from src.database import (
    AlertModel, AuditLogModel, AnalystModel, ThreatIntelFeed,
    SystemMetricsModel, get_db, init_db, close_db, async_session,
)
from src.auth import (
    TokenData, AnalystCreate, AnalystLogin, TokenResponse,
    create_access_token, create_refresh_token, decode_token, decode_access_token,
    hash_password, verify_password, verify_mfa_token, generate_mfa_secret,
    build_otpauth_url, get_current_analyst,
    generate_hmac, REFRESH_TOKEN_EXPIRE_DAYS, ACCESS_TOKEN_EXPIRE_MINUTES,
    set_auth_cookies, clear_auth_cookies,
    ACCESS_TOKEN_COOKIE, REFRESH_TOKEN_COOKIE,
)
from src.audit_chain import AuditChain
from src.reports import build_period_report_pdf, encrypt_pdf_with_pgp
from src.stix_taxii import alert_to_stix_bundle
from src.crypto_utils import encrypt_data, decrypt_data, encrypt_sensitive_field, decrypt_sensitive_field, hash_identifier
from src.cache import (
    get_redis, close_redis, check_rate_limit, cache_get, cache_set,
    register_refresh_jti, is_refresh_jti_valid, revoke_refresh_jti,
    revoke_all_refresh_for_user,
)
from pydantic import BaseModel, Field
from src.models import (
    AlertLevel, AlertStatus, AlertResponse, AlertsResponse,
    AuditEntry, AuditLogResponse, SystemStats, ReviewRequest, ReviewResponse,
    OrchestratorResponse, AnalystReport, ThreatIndicator,
)
from sqlalchemy import select, func, desc, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_START_TIME = time.time()

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
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)

# Security
security = HTTPBearer(auto_error=False)

# Paths excluidos del rate limiter (probes de plataforma: K8s, Docker, etc.)
# Siguen recibiendo headers de seguridad pero NO consumen ni cuentan en el contador.
RATE_LIMIT_EXEMPT_PATHS: frozenset[str] = frozenset({
    "/api/health/live",
    "/api/health/ready",
})

RATE_LIMITS: dict[str, tuple[int, int]] = {
    "/api/auth/login": (5, 60),
    "/api/auth/refresh": (10, 60),
    "/api/auth/logout": (10, 60),
    "/api/analyze": (10, 60),
    "/api/analyze/async": (10, 60),
    "/api/alerts": (100, 60),
    "/api/audit-log": (30, 60),
    "/api/reports/period": (5, 60),
    "/api/alerts/export.stix": (10, 60),
    "/api/analysts": (20, 60),
    "/api/analysts/me": (30, 60),
    "/api/metrics": (20, 60),
}
DEFAULT_RATE_LIMIT = (100, 60)


# ─────────────────────────────────────────────────────────────────────────────
# Middleware de seguridad
# ─────────────────────────────────────────────────────────────────────────────
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Inyecta headers de seguridad HTTP en todas las respuestas."""
    path = request.url.path
    rate_limit_exempt = path in RATE_LIMIT_EXEMPT_PATHS

    # Rate limiting por IP (saltar para health probes de plataforma)
    rate_info: dict | None = None
    allowed = True
    if not rate_limit_exempt:
        client_ip = request.client.host if request.client else "unknown"
        max_req, window_sec = RATE_LIMITS.get(path, DEFAULT_RATE_LIMIT)
        allowed, rate_info = await check_rate_limit(client_ip, max_requests=max_req, window_seconds=window_sec)

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=(), clipboard=()"

    if not allowed and rate_info is not None:
        return JSONResponse(
            status_code=429,
            content={"detail": "Demasiadas peticiones"},
            headers={"Retry-After": str(rate_info["reset"])},
        )

    # Añadir headers de rate limit (solo cuando aplica)
    if rate_info is not None:
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
class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class MFAConfirmRequest(BaseModel):
    token: str = Field(..., min_length=6, max_length=8)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=8, max_length=256)
    new_password: str = Field(..., min_length=12, max_length=256)


class PeriodReportRequest(BaseModel):
    date_from: str
    date_to: str
    classification: Optional[str] = None
    recipient_pgp_pubkey: Optional[str] = None


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(credentials: AnalystLogin, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    """Autenticación de analista con JWT + MFA TOTP opcional."""
    result = await db.execute(
        select(AnalystModel).where(AnalystModel.username == credentials.username)
    )
    analyst = result.scalar_one_or_none()

    if not analyst or not verify_password(credentials.password, analyst.password_hash):
        if analyst:
            analyst.failed_login_attempts = (analyst.failed_login_attempts or 0) + 1
            if analyst.failed_login_attempts >= 5:
                analyst.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
                analyst.failed_login_attempts = 0
            await db.commit()
            await _add_audit_entry(
                db=db,
                analyst_id=analyst.id,
                agent="AUTH",
                action_type="login_failed",
                details=f"username={credentials.username} ip={request.client.host if request.client else 'unknown'} attempts={analyst.failed_login_attempts}",
                ip_address=request.client.host if request.client else None,
            )
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # Cuenta activa
    if not analyst.is_active:
        raise HTTPException(status_code=403, detail="Cuenta deshabilitada")

    # Bloqueo temporal
    if analyst.locked_until and analyst.locked_until > datetime.now(timezone.utc):
        raise HTTPException(status_code=403, detail="Cuenta bloqueada. Intenta más tarde.")

    # Si requiere cambio de contraseña, no permitir login normal
    if getattr(analyst, "password_change_required", False):
        raise HTTPException(
            status_code=403,
            detail="Cambio de contraseña obligatorio. Use POST /api/analysts/me/password",
        )

    # MFA TOTP real (RFC 6238)
    if analyst.mfa_enabled:
        if not credentials.mfa_token:
            raise HTTPException(status_code=401, detail="Token MFA requerido")
        secret_plain = decrypt_sensitive_field(analyst.mfa_secret) or ""
        if not verify_mfa_token(secret_plain, credentials.mfa_token):
            raise HTTPException(status_code=401, detail="Token MFA inválido")

    token_data = {
        "sub": analyst.username,
        "role": analyst.role,
        "clearance": analyst.clearance_level,
        "analyst_id": analyst.id,
    }
    access_token = create_access_token(token_data)
    refresh_token_str, jti = create_refresh_token(token_data)

    # Persistir jti en Redis para revocación/rotación
    await register_refresh_jti(
        jti=jti,
        analyst_id=analyst.id,
        ttl_seconds=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
    )

    analyst.last_login = datetime.now(timezone.utc)
    analyst.failed_login_attempts = 0
    await db.commit()

    await _add_audit_entry(
        db=db,
        analyst_id=analyst.id,
        agent="AUTH",
        action_type="login_success",
        details=f"username={analyst.username} ip={request.client.host if request.client else 'unknown'}",
    )

    set_auth_cookies(response, access_token, refresh_token_str)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@app.post("/api/auth/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(request: Request, response: Response, body: RefreshRequest = None):
    """Refresca el access token rotando el refresh (revoca el anterior)."""
    raw_token = body.refresh_token if body else request.cookies.get(REFRESH_TOKEN_COOKIE)
    if not raw_token:
        raise HTTPException(status_code=401, detail="Refresh token requerido")
    try:
        payload = decode_token(raw_token)
    except HTTPException:
        raise
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Refresh token inválido")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Tipo de token inválido")

    jti = payload.get("jti")
    analyst_id = payload.get("analyst_id")
    if not jti or not analyst_id:
        raise HTTPException(status_code=401, detail="Refresh token inválido (sin jti)")

    stored_analyst_id = await is_refresh_jti_valid(jti)
    if not stored_analyst_id or stored_analyst_id != analyst_id:
        raise HTTPException(status_code=401, detail="Refresh token revocado o desconocido")

    # Rotación: revocar antiguo, emitir nuevo
    await revoke_refresh_jti(jti, analyst_id=analyst_id)

    new_token_data = {
        "sub": payload.get("sub"),
        "role": payload.get("role"),
        "clearance": payload.get("clearance"),
        "analyst_id": analyst_id,
    }
    new_access = create_access_token(new_token_data)
    new_refresh, new_jti = create_refresh_token(new_token_data)
    await register_refresh_jti(
        jti=new_jti,
        analyst_id=analyst_id,
        ttl_seconds=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
    )

    set_auth_cookies(response, new_access, new_refresh)

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@app.post("/api/auth/logout", status_code=204)
async def logout(request: Request, response: Response, body: LogoutRequest = None):
    """Revoca un refresh token específico."""
    raw_token = body.refresh_token if body else request.cookies.get(REFRESH_TOKEN_COOKIE)
    if raw_token:
        try:
            payload = decode_token(raw_token)
        except HTTPException:
            clear_auth_cookies(response)
            return
        if payload.get("type") == "refresh":
            jti = payload.get("jti")
            analyst_id = payload.get("analyst_id")
            if jti:
                await revoke_refresh_jti(jti, analyst_id=analyst_id)
    clear_auth_cookies(response)
    return


@app.post("/api/auth/logout-all", status_code=204)
async def logout_all(current: TokenData = Depends(get_current_analyst)):
    """Revoca todos los refresh tokens activos del analista actual."""
    await revoke_all_refresh_for_user(current.analyst_id)
    return


# ─────────────────────────────────────────────────────────────────────────────
# MFA — Enrolamiento TOTP (RFC 6238)
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/analysts/me/mfa/enroll")
async def mfa_enroll(
    db: AsyncSession = Depends(get_db),
    current: TokenData = Depends(get_current_analyst),
):
    """
    Genera y almacena (cifrado) un secreto MFA para el analista actual.
    Devuelve el otpauth_url y el secreto en claro para escanear con la app
    autenticadora. El secreto en claro SOLO se devuelve aquí; nunca se vuelve
    a exponer. El analista debe confirmar con /mfa/confirm para activar MFA.
    """
    result = await db.execute(
        select(AnalystModel).where(AnalystModel.id == current.analyst_id)
    )
    analyst = result.scalar_one_or_none()
    if not analyst:
        raise HTTPException(status_code=404, detail="Analista no encontrado")
    if analyst.mfa_enabled:
        raise HTTPException(status_code=409, detail="MFA ya está activado")

    secret = generate_mfa_secret()
    analyst.mfa_secret = encrypt_sensitive_field(secret)
    analyst.mfa_enabled = False  # se activa solo tras /confirm
    await db.commit()

    otpauth_url = build_otpauth_url(username=analyst.username, secret=secret, issuer="VIGIA")

    await _add_audit_entry(
        db=db,
        analyst_id=analyst.id,
        agent="AUTH",
        action_type="mfa_enroll_start",
        details=f"username={analyst.username}",
    )

    return {
        "otpauth_url": otpauth_url,
        "secret_b32": secret,
    }


@app.post("/api/analysts/me/mfa/confirm")
async def mfa_confirm(
    body: MFAConfirmRequest,
    db: AsyncSession = Depends(get_db),
    current: TokenData = Depends(get_current_analyst),
):
    """Confirma el enrolamiento MFA validando un primer código TOTP."""
    result = await db.execute(
        select(AnalystModel).where(AnalystModel.id == current.analyst_id)
    )
    analyst = result.scalar_one_or_none()
    if not analyst or not analyst.mfa_secret:
        raise HTTPException(status_code=400, detail="No hay enrolamiento MFA pendiente")

    secret_plain = decrypt_sensitive_field(analyst.mfa_secret) or ""
    if not verify_mfa_token(secret_plain, body.token):
        raise HTTPException(status_code=401, detail="Código TOTP inválido")

    analyst.mfa_enabled = True
    await db.commit()

    await _add_audit_entry(
        db=db,
        analyst_id=analyst.id,
        agent="AUTH",
        action_type="mfa_enroll_confirm",
        details=f"username={analyst.username}",
    )

    return {"mfa_enabled": True}


# ─────────────────────────────────────────────────────────────────────────────
# Cambio de contraseña (incluido el caso del admin bootstrap)
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/analysts/me/password")
async def change_password(
    body: PasswordChangeRequest,
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Cambia la contraseña del analista actual.
    Permite cambiar la contraseña incluso cuando password_change_required=True
    (el caso del admin tras bootstrap), validando con la contraseña actual.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="No autorizado")
    # Validar token sin invocar get_current_analyst (que ya verifica access)
    token_data = decode_access_token(credentials.credentials)

    result = await db.execute(
        select(AnalystModel).where(AnalystModel.id == token_data.analyst_id)
    )
    analyst = result.scalar_one_or_none()
    if not analyst:
        raise HTTPException(status_code=404, detail="Analista no encontrado")

    if not verify_password(body.current_password, analyst.password_hash):
        raise HTTPException(status_code=401, detail="Contraseña actual incorrecta")

    if body.current_password == body.new_password:
        raise HTTPException(status_code=400, detail="La nueva contraseña debe ser distinta")

    analyst.password_hash = hash_password(body.new_password)
    if hasattr(analyst, "password_change_required"):
        analyst.password_change_required = False
    await db.commit()

    # Revocar todas las sesiones existentes del analista por seguridad
    await revoke_all_refresh_for_user(analyst.id)

    await _add_audit_entry(
        db=db,
        analyst_id=analyst.id,
        agent="AUTH",
        action_type="password_changed",
        details=f"username={analyst.username}",
    )

    return {"success": True, "message": "Contraseña actualizada. Vuelva a iniciar sesión."}


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
# Health probes para orquestadores (Docker, K8s) — sin auth, sin rate limit
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/health/live")
async def health_live():
    """
    Liveness probe: el proceso está vivo y respondiendo.
    No toca DB ni Redis. Si responde 200, el contenedor NO debe ser reiniciado.
    """
    return {"status": "alive"}


@app.get("/api/health/ready")
async def health_ready(db: AsyncSession = Depends(get_db)):
    """
    Readiness probe: el servicio puede atender tráfico real.
    Comprueba DB (SELECT 1) y Redis (PING) con timeout corto.
    Devuelve 503 si alguna dependencia crítica falla.
    """
    db_status = "ok"
    redis_status = "ok"

    # DB: SELECT 1 con timeout corto
    try:
        await asyncio.wait_for(db.execute(text("SELECT 1")), timeout=2.0)
    except Exception:
        db_status = "error"

    # Redis: PING con timeout corto
    try:
        redis = await get_redis()
        await asyncio.wait_for(redis.ping(), timeout=2.0)
    except Exception:
        redis_status = "error"

    if db_status == "ok" and redis_status == "ok":
        return {"status": "ready", "db": db_status, "redis": redis_status}

    return JSONResponse(
        status_code=503,
        content={"status": "not_ready", "db": db_status, "redis": redis_status},
    )


@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    token = websocket.query_params.get("token", "")
    if not token:
        await websocket.close(code=1008, reason="Token requerido")
        return
    try:
        decode_access_token(token)
    except Exception:
        await websocket.close(code=1008, reason="Token inválido")
        return
    await websocket.accept()
    seen_ids: set[str] = set()
    try:
        while True:
            async with async_session() as session:
                result = await session.execute(
                    select(AlertModel)
                    .where(AlertModel.status == AlertStatus.PENDIENTE)
                    .order_by(desc(AlertModel.created_at))
                    .limit(50)
                )
                alerts = result.scalars().all()
                for alert in alerts:
                    if alert.id not in seen_ids:
                        seen_ids.add(alert.id)
                        indicators = json.loads(alert.indicators) if alert.indicators else []
                        payload = {
                            "type": "new_alert",
                            "id": alert.id,
                            "platform": alert.platform,
                            "content_excerpt": alert.content_excerpt,
                            "risk_score": alert.risk_score,
                            "risk_level": alert.risk_level,
                            "indicators": indicators,
                            "created_at": alert.created_at.isoformat() if alert.created_at else None,
                        }
                        await websocket.send_json(payload)
                if len(seen_ids) > 5000:
                    seen_ids.clear()
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        logger.info("WebSocket /ws/alerts desconectado")
    except Exception as exc:
        logger.error("Error en WebSocket /ws/alerts: %s", exc, exc_info=True)
        try:
            await websocket.close(code=1011)
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints de Alertas (Requieren autenticación)
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/health", response_model=SystemStats)
async def health(
    db: AsyncSession = Depends(get_db),
    current: TokenData = Depends(get_current_analyst),
):
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
        items.append(_alert_to_dict(alert))

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
    analyst_notes = decrypt_sensitive_field(alert.analyst_notes_encrypted) if alert.analyst_notes_encrypted else None

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
    alert.analyst_notes_encrypted = notes_encrypted

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


@app.post("/api/analyze/async", status_code=202)
async def run_analysis_async(
    objective: str = Query(..., min_length=5, max_length=500),
    platforms: Optional[str] = Query(None),
    max_results: int = Query(20, ge=1, le=1000),
    current: TokenData = Depends(get_current_analyst),
):
    """Lanza un análisis OSINT/SOCMINT asíncrono vía worker ARQ."""
    from arq import create_pool
    from arq.connections import RedisSettings

    if current.clearance not in ["SECRET", "TOP_SECRET"]:
        raise HTTPException(status_code=403, detail="Requiere nivel de habilitación SECRET+")

    platform_list = None
    if platforms:
        platform_list = [p.strip().lower() for p in platforms.split(",") if p.strip()]

    redis_settings = RedisSettings(
        host=os.environ.get("REDIS_HOST", "redis"),
        port=int(os.environ.get("REDIS_PORT", "6379")),
        password=os.environ.get("REDIS_PASSWORD", ""),
    )
    redis_pool = await create_pool(redis_settings)
    job = await redis_pool.enqueue_job(
        "run_analysis_worker",
        objective,
        platform_list,
        max_results,
        current.analyst_id,
    )
    return {"job_id": job.job_id, "status": "queued"}


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints de Informes, Exportación STIX, Perfil y Métricas
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/reports/period")
async def generate_period_report(
    body: PeriodReportRequest,
    db: AsyncSession = Depends(get_db),
    current: TokenData = Depends(get_current_analyst),
):
    date_from = body.date_from
    date_to = body.date_to
    classification = body.classification or "CONFIDENTIAL"

    result = await db.execute(
        select(AlertModel)
        .where(
            and_(
                AlertModel.created_at >= date_from,
                AlertModel.created_at <= date_to,
            )
        )
        .order_by(desc(AlertModel.created_at))
    )
    alerts = result.scalars().all()

    alerts_data = [_alert_to_dict(a) for a in alerts]

    pdf_bytes = build_period_report_pdf(
        alerts=alerts_data,
        date_from=date_from,
        date_to=date_to,
        classification=classification,
    )

    content_type = "application/pdf"
    safe_from = "".join(c for c in date_from if c.isalnum() or c in "-_")
    safe_to = "".join(c for c in date_to if c.isalnum() or c in "-_")
    filename = f"vigia_informe_{safe_from}_{safe_to}.pdf"

    if body.recipient_pgp_pubkey:
        pdf_bytes = encrypt_pdf_with_pgp(pdf_bytes, body.recipient_pgp_pubkey)
        content_type = "application/octet-stream"
        filename = f"vigia_informe_{safe_from}_{safe_to}.pdf.gpg"

    await _add_audit_entry(
        db=db,
        analyst_id=current.analyst_id,
        agent="ANALYST",
        action_type="report_period_generated",
        details=f"from={date_from} to={date_to} alerts={len(alerts_data)} classification={classification}",
    )

    return Response(
        content=pdf_bytes,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/alerts/export.stix")
async def export_alerts_stix(
    ids: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current: TokenData = Depends(get_current_analyst),
):
    if ids:
        id_list = [i.strip() for i in ids.split(",") if i.strip()]
        result = await db.execute(
            select(AlertModel).where(AlertModel.id.in_(id_list))
        )
    else:
        result = await db.execute(
            select(AlertModel)
            .order_by(desc(AlertModel.created_at))
            .limit(500)
        )
    alerts = result.scalars().all()

    combined_objects = []
    for alert in alerts:
        alert_dict = _alert_to_dict(alert)
        bundle = alert_to_stix_bundle(alert_dict)
        combined_objects.extend(bundle.get("objects", []))

    combined_bundle = {
        "type": "bundle",
        "id": f"bundle--{str(uuid.uuid4())}",
        "objects": combined_objects,
    }

    await _add_audit_entry(
        db=db,
        analyst_id=current.analyst_id,
        agent="ANALYST",
        action_type="stix_export",
        details=f"alerts_exported={len(alerts)}",
    )

    return JSONResponse(content=combined_bundle)


@app.get("/api/analysts/me")
async def get_current_analyst_profile(
    db: AsyncSession = Depends(get_db),
    current: TokenData = Depends(get_current_analyst),
):
    result = await db.execute(
        select(AnalystModel).where(AnalystModel.id == current.analyst_id)
    )
    analyst = result.scalar_one_or_none()
    if not analyst:
        raise HTTPException(status_code=404, detail="Analista no encontrado")

    return {
        "id": analyst.id,
        "username": analyst.username,
        "email": analyst.email,
        "full_name": analyst.full_name,
        "role": analyst.role,
        "clearance_level": analyst.clearance_level,
        "is_active": analyst.is_active,
        "mfa_enabled": analyst.mfa_enabled,
        "last_login": analyst.last_login.isoformat() if analyst.last_login else None,
        "created_at": analyst.created_at.isoformat() if analyst.created_at else None,
    }


@app.get("/api/metrics")
async def prometheus_metrics(
    db: AsyncSession = Depends(get_db),
    current: TokenData = Depends(get_current_analyst),
):
    uptime_seconds = time.time() - _START_TIME

    total_result = await db.execute(select(func.count(AlertModel.id)))
    total_alerts = total_result.scalar() or 0

    by_level_result = await db.execute(
        select(AlertModel.risk_level, func.count(AlertModel.id))
        .group_by(AlertModel.risk_level)
    )
    by_level = {level: count for level, count in by_level_result.all()}

    pending_result = await db.execute(
        select(func.count(AlertModel.id)).where(AlertModel.status == AlertStatus.PENDIENTE)
    )
    pending_alerts = pending_result.scalar() or 0

    lines = [
        "# HELP vigia_alerts_total Total de alertas en el sistema",
        "# TYPE vigia_alerts_total counter",
        f"vigia_alerts_total {total_alerts}",
        "",
        "# HELP vigia_alerts_pending Alertas pendientes de revisión",
        "# TYPE vigia_alerts_pending gauge",
        f"vigia_alerts_pending {pending_alerts}",
        "",
        "# HELP vigia_alerts_by_level Alertas por nivel de riesgo",
        "# TYPE vigia_alerts_by_level gauge",
    ]
    for level in ("VERDE", "AMARILLO", "NARANJA", "ROJO"):
        lines.append(f'vigia_alerts_by_level{{level="{level}"}} {by_level.get(level, 0)}')

    lines.extend([
        "",
        "# HELP vigia_uptime_seconds Segundos desde el inicio del servicio",
        "# TYPE vigia_uptime_seconds gauge",
        f"vigia_uptime_seconds {uptime_seconds:.2f}",
    ])

    return PlainTextResponse(content="\n".join(lines) + "\n", media_type="text/plain; version=0.0.4")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _alert_to_dict(alert: AlertModel) -> dict:
    indicators = json.loads(alert.indicators) if alert.indicators else []
    return {
        "id": alert.id,
        "platform": alert.platform,
        "content_excerpt": alert.content_excerpt,
        "risk_score": alert.risk_score,
        "risk_level": alert.risk_level,
        "status": alert.status,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
        "indicators": indicators,
    }


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

    chain_hash = await AuditChain.anchor(entry_id, timestamp.isoformat(), agent, action_type, details)

    entry = AuditLogModel(
        id=entry_id,
        timestamp=timestamp,
        session_id=None,
        agent=agent,
        action_type=action_type,
        target_id=target_id,
        alert_id=alert_id,
        details=details,
        ip_address=ip_address,
        analyst_id=analyst_id,
        hmac_signature=hmac_signature,
        chain_hash=chain_hash,
    )
    db.add(entry)
    await db.commit()
    logger.info("[AUDIT] %s | %s | %s", agent, action_type, details)
