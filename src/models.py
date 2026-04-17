"""
Modelos Pydantic para el sistema VIGÍA — OSINT/SOCMINT Monitor
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re


class AlertLevel(str, Enum):
    VERDE = "VERDE"
    AMARILLO = "AMARILLO"
    NARANJA = "NARANJA"
    ROJO = "ROJO"


class AlertStatus(str, Enum):
    PENDIENTE = "PENDIENTE"
    ESCALADA = "ESCALADA"
    ARCHIVADA = "ARCHIVADA"
    FALSO_POSITIVO = "FALSO_POSITIVO"


class ReviewAction(str, Enum):
    ESCALAR = "ESCALAR"
    ARCHIVAR = "ARCHIVAR"
    FALSO_POSITIVO = "FALSO_POSITIVO"


class IndicatorType(str, Enum):
    LLAMADA_VIOLENCIA = "llamada_violencia"
    COORDINACION_ATAQUE = "coordinacion_ataque"
    GLORIFICACION_TERRORISMO = "glorificacion_terrorismo"
    RECLUTAMIENTO = "reclutamiento"
    AMENAZA_DIRECTA = "amenaza_directa"


class ThreatIndicator(BaseModel):
    type: IndicatorType
    value: str = Field(..., max_length=500, description="Fragmento de texto que disparó el indicador")
    explanation: str = Field(..., max_length=1000, description="Por qué este fragmento es un indicador")
    confidence: float = Field(ge=0.0, le=1.0)


class SocialPost(BaseModel):
    id: str = Field(..., max_length=128)
    platform: str = Field(..., max_length=64)
    content: str = Field(..., max_length=10_000)
    author_id_hash: str = Field(..., max_length=64, description="SHA-256 del author_id original, nunca el ID en claro")
    timestamp: datetime
    url: str = Field(..., max_length=2048)
    is_public: bool = True
    language: Optional[str] = Field(None, max_length=10)

    @field_validator("author_id_hash")
    @classmethod
    def validate_author_hash(cls, v: str) -> str:
        """El hash debe ser un SHA-256 hexadecimal de 64 caracteres."""
        if not re.fullmatch(r"[0-9a-f]{64}", v):
            raise ValueError("author_id_hash debe ser un SHA-256 hex de 64 caracteres")
        return v


class ThreatAssessment(BaseModel):
    id: str
    post_id: str
    indicators_found: list[ThreatIndicator]
    risk_score: float = Field(ge=0.0, le=1.0)
    alert_level: AlertLevel
    requires_human_review: bool
    assessment_timestamp: datetime
    model_version: str = "1.0.0"


class AnalystReport(BaseModel):
    id: str = Field(..., max_length=128)
    assessment_id: str = Field(..., max_length=128)
    analyst_id: str = Field(..., min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_\-]+$")
    action: ReviewAction
    notes: str = Field(..., min_length=10, max_length=2000)
    timestamp: datetime


class AlertResponse(BaseModel):
    id: str
    platform: str
    content_excerpt: str
    content_full: str
    indicators: list[ThreatIndicator]
    risk_score: float
    risk_level: AlertLevel
    status: AlertStatus
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    analyst_notes: Optional[str] = None


class AlertListItem(BaseModel):
    id: str
    platform: str
    content_excerpt: str
    indicators: list[ThreatIndicator]
    risk_score: float
    risk_level: AlertLevel
    status: AlertStatus
    created_at: datetime


class AlertsResponse(BaseModel):
    items: list[AlertListItem]
    total: int
    page: int
    page_size: int


class ReviewRequest(BaseModel):
    action: ReviewAction
    notes: str = Field(..., min_length=10, max_length=2000)
    analyst_id: str = Field(..., min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_\-]+$")


class ReviewResponse(BaseModel):
    success: bool
    message: str


class AuditEntry(BaseModel):
    id: str
    timestamp: datetime
    agent: str
    action_type: str
    target_id: Optional[str] = None
    details: str
    alert_id: Optional[str] = None


class AuditLogResponse(BaseModel):
    items: list[AuditEntry]
    total: int
    page: int
    page_size: int


class SystemStats(BaseModel):
    alerts_today: int
    pending_review: int
    by_level: dict[str, int]
    system_status: str = "online"


class OrchestratorAction(BaseModel):
    step: int
    agent: str
    task: str
    status: str = "pending"


class OrchestratorResponse(BaseModel):
    objective: str
    selected_agents: list[str]
    reasoning_summary: str
    actions: list[OrchestratorAction]
    final_recommendation: str
    requires_human_approval: bool
    audit_note: str
