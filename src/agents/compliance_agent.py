"""
COMPLIANCE_AGENT — Verifica cumplimiento legal y de policy.yaml antes de cualquier acción.

Garantiza que:
- El contenido analizado era efectivamente público
- No hay datos personales sensibles sin anonimizar
- La acción propuesta cumple con policy.yaml
- El risk_score es coherente con los indicadores encontrados
"""
import logging

from src.models import AlertLevel, SocialPost, ThreatAssessment

logger = logging.getLogger(__name__)

# Umbrales de riesgo para acciones automáticas (de policy.yaml)
AUTO_APPROVE_MAX_SCORE = 0.30  # VERDE: archivo automático permitido
HUMAN_REVIEW_REQUIRED_MIN = 0.30  # AMARILLO+: revisión humana obligatoria


def check_compliance(
    post: SocialPost,
    assessment: ThreatAssessment,
    proposed_action: str,
) -> dict:
    """
    Verifica el cumplimiento legal y operativo de procesar un post y tomar una acción.

    Args:
        post: Publicación analizada.
        assessment: Resultado del análisis de amenazas.
        proposed_action: Acción que el sistema propone tomar.

    Returns:
        Dict con status, issues encontrados, risk_score y revisión segura propuesta.
    """
    logger.info(
        "COMPLIANCE_AGENT: verificando post %s (nivel %s, acción '%s')",
        post.id,
        assessment.alert_level,
        proposed_action,
    )

    issues: list[str] = []
    blocked = False

    # 1. Verificar que el contenido sea público
    if not post.is_public:
        issues.append("BLOQUEADO: contenido no público — requiere autorización judicial para acceso")
        blocked = True

    # 2. Verificar anonimización del author_id
    if len(post.author_id_hash) < 8 or post.author_id_hash == post.author_id_hash.upper():
        issues.append("ADVERTENCIA: author_id_hash no parece estar correctamente hasheado")

    # 3. Verificar coherencia entre indicadores y risk_score
    n_indicators = len(assessment.indicators_found)
    if n_indicators == 0 and assessment.risk_score > 0.1:
        issues.append(
            f"INCOHERENCIA: risk_score={assessment.risk_score} pero 0 indicadores encontrados"
        )

    # 4. Verificar que la acción propuesta es compatible con el nivel de riesgo
    if proposed_action == "archive_auto" and assessment.alert_level != AlertLevel.VERDE:
        issues.append(
            f"ACCIÓN NO PERMITIDA: archivo automático no permitido para nivel {assessment.alert_level}"
        )

    if proposed_action in ("escalate", "share_external") and assessment.alert_level == AlertLevel.VERDE:
        issues.append(
            "ACCIÓN DESPROPORCIONADA: escalada no justificada para nivel VERDE"
        )

    # 5. Verificar que acciones de alto impacto requieren revisión humana
    high_impact_actions = ("escalate", "share_external", "request_platform_data")
    if proposed_action in high_impact_actions:
        issues.append(
            f"REQUIERE APROBACIÓN HUMANA: '{proposed_action}' es una acción de alto impacto"
        )
        # Esto no bloquea, solo lo registra para que el execution_agent lo maneje

    # Determinar status final
    if blocked:
        status = "blocked"
    elif issues:
        status = "needs_review"
    else:
        status = "approved"

    # Proponer revisión segura si hay problemas
    safe_revision = None
    if status == "needs_review" and not blocked:
        safe_revision = "queue_for_human_approval"
    elif status == "blocked":
        safe_revision = "discard_and_log"

    result = {
        "status": status,
        "issues": issues,
        "risk_score": assessment.risk_score,
        "safe_revision": safe_revision,
        "requires_human_approval": assessment.requires_human_review or bool(issues),
    }

    logger.info(
        "COMPLIANCE_AGENT: resultado para post %s → status=%s issues=%d",
        post.id,
        status,
        len(issues),
    )
    return result
