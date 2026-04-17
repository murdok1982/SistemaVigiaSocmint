"""
EXECUTION_AGENT — Prepara y ejecuta las acciones aprobadas por compliance.

NUNCA publica ni interactúa en redes sociales.
Solo genera alertas para analistas humanos, programa revisiones
y registra el audit_log.
"""
import logging
import uuid
from datetime import datetime, timezone

from src.models import (
    AlertLevel,
    AlertStatus,
    AuditEntry,
    SocialPost,
    ThreatAssessment,
)

logger = logging.getLogger(__name__)


def prepare_execution(
    post: SocialPost,
    assessment: ThreatAssessment,
    compliance_result: dict,
) -> dict:
    """
    Prepara el payload de ejecución basado en el resultado del compliance check.

    Args:
        post: Publicación analizada.
        assessment: Resultado del análisis.
        compliance_result: Resultado del compliance check.

    Returns:
        Dict con la acción a ejecutar, payload y registro de auditoría.
    """
    logger.info(
        "EXECUTION_AGENT: preparando ejecución para post %s (nivel %s)",
        post.id,
        assessment.alert_level,
    )

    compliance_status = compliance_result.get("status", "needs_review")
    alert_level = assessment.alert_level

    # Determinar acción a ejecutar
    if compliance_status == "blocked":
        action = "skip"
        payload_summary = "Post descartado por compliance — contenido no público o violación de policy"
        requires_human_approval = False
        queue_priority = "none"

    elif alert_level == AlertLevel.VERDE and compliance_status == "approved":
        action = "archive"
        payload_summary = "Alerta nivel VERDE — archivada automáticamente, sin revisión requerida"
        requires_human_approval = False
        queue_priority = "low"

    elif alert_level == AlertLevel.AMARILLO:
        action = "queue_for_approval"
        payload_summary = "Alerta nivel AMARILLO — en cola de revisión estándar (48h)"
        requires_human_approval = True
        queue_priority = "standard"

    elif alert_level == AlertLevel.NARANJA:
        action = "queue_for_approval"
        payload_summary = "Alerta nivel NARANJA — en cola prioritaria (4h) + notificación a supervisor"
        requires_human_approval = True
        queue_priority = "high"

    else:  # ROJO
        action = "escalate_immediate"
        payload_summary = "Alerta nivel ROJO — escalada inmediata + notificación a cadena de mando"
        requires_human_approval = True
        queue_priority = "critical"

    # Generar registro de auditoría
    audit_entry = AuditEntry(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        agent="EXECUTION_AGENT",
        action_type=action,
        target_id=post.id,
        details=(
            f"post_id={post.id} platform={post.platform} "
            f"risk_score={assessment.risk_score:.4f} "
            f"alert_level={assessment.alert_level} "
            f"indicators={len(assessment.indicators_found)} "
            f"compliance={compliance_status} "
            f"action={action}"
        ),
        alert_id=assessment.id,
    )

    # Determinar status de la alerta
    if action in ("archive", "skip"):
        alert_status = AlertStatus.ARCHIVADA
    else:
        alert_status = AlertStatus.PENDIENTE

    result = {
        "action": action,
        "platform": post.platform,
        "payload_summary": payload_summary,
        "requires_human_approval": requires_human_approval,
        "queue_priority": queue_priority,
        "alert_status": alert_status,
        "audit_log": audit_entry.model_dump(mode="json"),
        "assessment_id": assessment.id,
    }

    logger.info(
        "EXECUTION_AGENT: acción='%s' prioridad='%s' para post %s",
        action,
        queue_priority,
        post.id,
    )
    return result
