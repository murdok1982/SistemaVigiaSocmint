"""
API FastAPI — Sistema VIGÍA OSINT/SOCMINT Monitor

Endpoints para el dashboard de analistas humanos.
Toda acción de revisión requiere identificación del analista.
"""
import logging
import os
import secrets
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Path, Query, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security.api_key import APIKeyHeader

from src.models import (
    AlertLevel,
    AlertResponse,
    AlertStatus,
    AlertsResponse,
    AuditEntry,
    AuditLogResponse,
    OrchestratorResponse,
    ReviewRequest,
    ReviewResponse,
    SystemStats,
    ThreatIndicator,
)
from src.orchestrator import VigiaOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Configuración de seguridad desde entorno
# ─────────────────────────────────────────────────────────────────────────────
_VIGIA_API_KEY: Optional[str] = os.environ.get("VIGIA_API_KEY")
_API_KEY_ENABLED: bool = bool(_VIGIA_API_KEY)

_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Rate limiting en memoria (prototipo — en producción usar Redis)
# Estructura: { ip: [(timestamp, endpoint), ...] }
_rate_limit_store: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT_WRITE_MAX = 10   # peticiones de escritura por ventana
_RATE_LIMIT_WRITE_WINDOW = 60  # segundos


def _get_client_ip(request: Request) -> str:
    """Extrae la IP real del cliente, considerando proxies confiables."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Tomar solo la primera IP (cliente original) — no confiar en toda la cadena
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate_limit(ip: str) -> None:
    """
    Verifica que la IP no haya superado el límite de peticiones de escritura.
    Lanza HTTPException 429 si se supera el límite.
    """
    now = time.monotonic()
    window_start = now - _RATE_LIMIT_WRITE_WINDOW
    # Limpiar entradas antiguas
    _rate_limit_store[ip] = [t for t in _rate_limit_store[ip] if t > window_start]
    if len(_rate_limit_store[ip]) >= _RATE_LIMIT_WRITE_MAX:
        logger.warning("RATE_LIMIT: IP=%s superó el límite de %d req/%ds", ip, _RATE_LIMIT_WRITE_MAX, _RATE_LIMIT_WRITE_WINDOW)
        raise HTTPException(
            status_code=429,
            detail="Demasiadas peticiones. Intenta de nuevo más tarde.",
            headers={"Retry-After": str(_RATE_LIMIT_WRITE_WINDOW)},
        )
    _rate_limit_store[ip].append(now)


def _verify_api_key(api_key: Optional[str] = Security(_API_KEY_HEADER)) -> None:
    """
    Verifica el API key en el header X-API-Key para endpoints de escritura.
    Si VIGIA_API_KEY no está configurada, la verificación se omite (modo desarrollo).
    Usa comparación en tiempo constante para evitar timing attacks.
    """
    if not _API_KEY_ENABLED:
        logger.warning("SECURITY: VIGIA_API_KEY no configurada — endpoints de escritura sin protección")
        return
    if api_key is None or not secrets.compare_digest(api_key, _VIGIA_API_KEY):
        raise HTTPException(status_code=401, detail="API key inválida o ausente")


def _sanitize_for_log(text: str, max_length: int = 200) -> str:
    """
    Sanitiza un string para incluirlo en logs.
    Elimina newlines y caracteres de control para prevenir log injection.
    Trunca a max_length caracteres.
    """
    sanitized = text.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    # Eliminar otros caracteres de control (U+0000–U+001F excepto los ya tratados)
    sanitized = "".join(c if ord(c) >= 0x20 else f"\\x{ord(c):02x}" for c in sanitized)
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "[TRUNCADO]"
    return sanitized


app = FastAPI(
    title="VIGÍA — Sistema OSINT/SOCMINT Monitor",
    description="API para análisis pasivo de amenazas en contenido público de redes sociales.",
    version="0.1.0",
    # Deshabilitar docs en producción configurando VIGIA_ENV=production
    docs_url=None if os.environ.get("VIGIA_ENV") == "production" else "/docs",
    redoc_url=None,
)

# CORS: origenes explícitos desde variable de entorno, con fallback para desarrollo
_raw_origins = os.environ.get("VIGIA_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Inyecta headers de seguridad HTTP en todas las respuestas."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; frame-ancestors 'none'"
    )
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler global: captura excepciones no controladas y devuelve un mensaje
    genérico sin exponer stack traces ni detalles internos del sistema.
    """
    # HTTPException tiene su propio handler en FastAPI — aquí solo caen las inesperadas
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    logger.error("ERROR no controlado en %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor. Contacta al administrador del sistema."},
    )

# ─────────────────────────────────────────────────────────────────────────────
# Almacenamiento en memoria (prototipo — en producción: PostgreSQL + SQLAlchemy)
# ─────────────────────────────────────────────────────────────────────────────
_alerts_db: dict[str, dict] = {}
_audit_db: list[dict] = []


def _add_audit_entry(agent: str, action_type: str, details: str, alert_id: Optional[str] = None) -> None:
    """Registra una entrada en el log de auditoría con sanitización anti-log-injection."""
    safe_details = _sanitize_for_log(details)
    safe_agent = _sanitize_for_log(agent, max_length=64)
    safe_action = _sanitize_for_log(action_type, max_length=64)
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": safe_agent,
        "action_type": safe_action,
        "target_id": alert_id,
        "details": safe_details,
        "alert_id": alert_id,
    }
    _audit_db.append(entry)
    logger.info("[AUDIT] %s | %s | %s", safe_agent, safe_action, safe_details)


def _seed_sample_alerts() -> None:
    """Carga alertas de muestra para demostración del prototipo."""
    if _alerts_db:
        return

    samples = [
        {
            "id": str(uuid.uuid4()),
            "platform": "Telegram",
            "content_excerpt": "Coordinar el ataque el próximo viernes. Punto de encuentro...",
            "content_full": "Coordinar el ataque el próximo viernes. Punto de encuentro: ya sabéis dónde. Traed el material acordado. La señal es la habitual.",
            "indicators": [
                {"type": "coordinacion_ataque", "value": "coordinar el ataque", "explanation": "Posible coordinación de acción violenta: 'coordinar el ataque'", "confidence": 0.85},
                {"type": "coordinacion_ataque", "value": "punto de encuentro", "explanation": "Posible coordinación de acción violenta: 'punto de encuentro'", "confidence": 0.75},
            ],
            "risk_score": 0.78,
            "risk_level": AlertLevel.ROJO,
            "status": AlertStatus.PENDIENTE,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "reviewed_at": None,
            "reviewed_by": None,
            "analyst_notes": None,
        },
        {
            "id": str(uuid.uuid4()),
            "platform": "Twitter",
            "content_excerpt": "Hay que destruir el sistema, no podemos seguir así. El cambio viene...",
            "content_full": "Hay que destruir el sistema, no podemos seguir así. El cambio viene por la fuerza, no hay otra opción.",
            "indicators": [
                {"type": "llamada_violencia", "value": "destruir el sistema", "explanation": "Llamada explícita a la violencia: 'destruir el sistema'", "confidence": 0.65},
            ],
            "risk_score": 0.52,
            "risk_level": AlertLevel.NARANJA,
            "status": AlertStatus.PENDIENTE,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "reviewed_at": None,
            "reviewed_by": None,
            "analyst_notes": None,
        },
        {
            "id": str(uuid.uuid4()),
            "platform": "Facebook",
            "content_excerpt": "Voy a mataros a todos si no cambian las cosas. Estoy al límite...",
            "content_full": "Voy a mataros a todos si no cambian las cosas. Estoy al límite y no tengo nada que perder.",
            "indicators": [
                {"type": "amenaza_directa", "value": "voy a mataros", "explanation": "Amenaza directa e identificable: 'voy a mataros'", "confidence": 0.90},
            ],
            "risk_score": 0.82,
            "risk_level": AlertLevel.ROJO,
            "status": AlertStatus.PENDIENTE,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "reviewed_at": None,
            "reviewed_by": None,
            "analyst_notes": None,
        },
        {
            "id": str(uuid.uuid4()),
            "platform": "Reddit",
            "content_excerpt": "A veces pienso que la única solución es la radical...",
            "content_full": "Estoy harto de todo esto. A veces pienso que la única solución es la radical.",
            "indicators": [],
            "risk_score": 0.18,
            "risk_level": AlertLevel.VERDE,
            "status": AlertStatus.ARCHIVADA,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "reviewed_at": None,
            "reviewed_by": None,
            "analyst_notes": None,
        },
    ]

    for alert in samples:
        _alerts_db[alert["id"]] = alert
        _add_audit_entry(
            "SYSTEM",
            "alert_created",
            f"platform={alert['platform']} level={alert['risk_level']} score={alert['risk_score']}",
            alert["id"],
        )


# Inicializar datos de muestra al arrancar
_seed_sample_alerts()


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/health", response_model=SystemStats)
async def health() -> SystemStats:
    """Estado del sistema y estadísticas generales."""
    by_level = {level.value: 0 for level in AlertLevel}
    pending = 0

    for alert in _alerts_db.values():
        level = alert["risk_level"]
        if isinstance(level, AlertLevel):
            by_level[level.value] += 1
        else:
            by_level[str(level)] = by_level.get(str(level), 0) + 1

        if alert["status"] == AlertStatus.PENDIENTE:
            pending += 1

    return SystemStats(
        alerts_today=len(_alerts_db),
        pending_review=pending,
        by_level=by_level,
        system_status="online",
    )


@app.get("/api/alerts", response_model=AlertsResponse)
async def list_alerts(
    risk_level: Optional[AlertLevel] = Query(None),
    platform: Optional[str] = Query(None),
    status: Optional[AlertStatus] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> AlertsResponse:
    """Lista de alertas con filtros opcionales."""
    alerts = list(_alerts_db.values())

    # Aplicar filtros
    if risk_level is not None:
        alerts = [a for a in alerts if a["risk_level"] == risk_level]
    if platform is not None:
        alerts = [a for a in alerts if a["platform"].lower() == platform.lower()]
    if status is not None:
        alerts = [a for a in alerts if a["status"] == status]

    # Ordenar por risk_score descendente
    alerts.sort(key=lambda a: a["risk_score"], reverse=True)

    # Paginación
    total = len(alerts)
    start = (page - 1) * page_size
    end = start + page_size
    page_alerts = alerts[start:end]

    items = []
    for a in page_alerts:
        indicators = [ThreatIndicator(**ind) if isinstance(ind, dict) else ind for ind in a["indicators"]]
        items.append({
            "id": a["id"],
            "platform": a["platform"],
            "content_excerpt": a["content_excerpt"],
            "indicators": indicators,
            "risk_score": a["risk_score"],
            "risk_level": a["risk_level"],
            "status": a["status"],
            "created_at": a["created_at"],
        })

    return AlertsResponse(items=items, total=total, page=page, page_size=page_size)


@app.get("/api/alerts/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: str = Path(..., max_length=128)) -> AlertResponse:
    """Detalle completo de una alerta."""
    alert = _alerts_db.get(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")

    indicators = [ThreatIndicator(**ind) if isinstance(ind, dict) else ind for ind in alert["indicators"]]

    return AlertResponse(
        id=alert["id"],
        platform=alert["platform"],
        content_excerpt=alert["content_excerpt"],
        content_full=alert["content_full"],
        indicators=indicators,
        risk_score=alert["risk_score"],
        risk_level=alert["risk_level"],
        status=alert["status"],
        created_at=alert["created_at"],
        reviewed_at=alert.get("reviewed_at"),
        reviewed_by=alert.get("reviewed_by"),
        analyst_notes=alert.get("analyst_notes"),
    )


@app.post("/api/alerts/{alert_id}/review", response_model=ReviewResponse)
async def review_alert(
    request: Request,
    body: ReviewRequest,
    alert_id: str = Path(..., max_length=128),
    _api_key: None = Security(_verify_api_key),
) -> ReviewResponse:
    """
    Registra la decisión del analista sobre una alerta.
    Requiere X-API-Key válida, identificación del analista y notas de justificación.
    """
    _check_rate_limit(_get_client_ip(request))

    # Rechazar alert_id con caracteres fuera del rango UUID para evitar path traversal
    if not alert_id.replace("-", "").isalnum():
        raise HTTPException(status_code=400, detail="ID de alerta inválido")

    alert = _alerts_db.get(alert_id)
    if not alert:
        # Respuesta genérica para no filtrar existencia de IDs
        raise HTTPException(status_code=404, detail="Alerta no encontrada")

    if alert["status"] != AlertStatus.PENDIENTE:
        raise HTTPException(
            status_code=409,
            detail="La alerta ya fue revisada",
        )

    # Mapear acción a status
    status_map = {
        "ESCALAR": AlertStatus.ESCALADA,
        "ARCHIVAR": AlertStatus.ARCHIVADA,
        "FALSO_POSITIVO": AlertStatus.FALSO_POSITIVO,
    }
    new_status = status_map.get(body.action, AlertStatus.ARCHIVADA)

    now = datetime.now(timezone.utc).isoformat()
    _alerts_db[alert_id]["status"] = new_status
    _alerts_db[alert_id]["reviewed_at"] = now
    _alerts_db[alert_id]["reviewed_by"] = body.analyst_id
    _alerts_db[alert_id]["analyst_notes"] = body.notes

    _add_audit_entry(
        "ANALYST",
        f"review_{body.action.lower()}",
        # Solo loguear longitud de las notas, no su contenido (puede contener datos sensibles)
        f"analista={body.analyst_id} accion={body.action} notas_len={len(body.notes)}",
        alert_id,
    )

    logger.info(
        "REVIEW: alerta %s → %s por analista %s",
        alert_id,
        new_status,
        body.analyst_id,
    )

    return ReviewResponse(
        success=True,
        message=f"Decisión registrada: {body.action} — {new_status}",
    )


@app.post("/api/analyze", response_model=OrchestratorResponse)
async def run_analysis(
    request: Request,
    objective: str = Query(..., min_length=5, max_length=500, description="Objetivo del análisis"),
    platforms: Optional[str] = Query(None, max_length=200, description="Plataformas separadas por coma"),
    max_results: int = Query(20, ge=1, le=100),
    _api_key: None = Security(_verify_api_key),
) -> OrchestratorResponse:
    """
    Lanza un ciclo completo de análisis OSINT/SOCMINT.
    Requiere X-API-Key válida. Las alertas generadas quedan en la cola de revisión humana.
    """
    _check_rate_limit(_get_client_ip(request))

    # Validar y normalizar la lista de plataformas
    _ALLOWED_PLATFORMS = {"twitter", "telegram", "facebook", "reddit", "web"}
    platform_list: Optional[list[str]] = None
    if platforms:
        raw_platforms = [p.strip().lower() for p in platforms.split(",") if p.strip()]
        platform_list = [p for p in raw_platforms if p in _ALLOWED_PLATFORMS]
        if not platform_list:
            raise HTTPException(status_code=400, detail="Ninguna plataforma válida especificada")

    orchestrator = VigiaOrchestrator()
    result = await orchestrator.run_analysis_pipeline(
        objective=objective,
        platforms=platform_list,
        max_results=max_results,
    )

    # Persistir alertas usando los datos ya calculados por el orquestador
    now = datetime.now(timezone.utc).isoformat()
    alerts_created = 0
    for entry in orchestrator._results:
        alert_data = entry.get("_alert_data")
        if not alert_data or entry.get("action") == "skip":
            continue

        alert_id = alert_data["id"]
        alert_status = (
            AlertStatus.ARCHIVADA if alert_data["action"] == "archive" else AlertStatus.PENDIENTE
        )

        _alerts_db[alert_id] = {
            "id": alert_id,
            "platform": alert_data["platform"],
            "content_excerpt": alert_data["content_excerpt"],
            "content_full": alert_data["content_full"],
            "indicators": alert_data["indicators"],
            "risk_score": alert_data["risk_score"],
            "risk_level": alert_data["risk_level"],
            "status": alert_status,
            "created_at": now,
            "reviewed_at": None,
            "reviewed_by": None,
            "analyst_notes": None,
        }
        _add_audit_entry(
            "ORCHESTRATOR",
            "alert_created",
            f"platform={alert_data['platform']} level={alert_data['risk_level']} score={alert_data['risk_score']:.4f}",
            alert_id,
        )
        alerts_created += 1

    # Sanitizar el objetivo antes de loguearlo (viene de input externo)
    _add_audit_entry(
        "ORCHESTRATOR",
        "analysis_run",
        f"objetivo='{_sanitize_for_log(objective)}' plataformas={platform_list} max={max_results} alertas_creadas={alerts_created}",
    )

    return result


@app.get("/api/audit-log", response_model=AuditLogResponse)
async def get_audit_log(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    agent: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> AuditLogResponse:
    """Log de auditoría completo con filtros."""
    entries = list(_audit_db)

    if agent:
        entries = [e for e in entries if agent.lower() in e["agent"].lower()]
    if action_type:
        entries = [e for e in entries if action_type.lower() in e["action_type"].lower()]

    # Ordenar por timestamp descendente
    entries.sort(key=lambda e: e["timestamp"], reverse=True)

    total = len(entries)
    start = (page - 1) * page_size
    items = [AuditEntry(**e) for e in entries[start : start + page_size]]

    return AuditLogResponse(items=items, total=total, page=page, page_size=page_size)
