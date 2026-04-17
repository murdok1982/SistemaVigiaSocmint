"""
ANALYSIS_AGENT — Análisis lingüístico de contenido para detección de indicadores de amenaza.

Evalúa el contenido de publicaciones públicas contra patrones de amenaza conocidos,
calcula un risk_score y determina el nivel de alerta correspondiente.

NUNCA clasifica como amenaza por: religión, etnia, política sin violencia.
"""
import logging
import re
import uuid
from datetime import datetime, timezone

from src.agents.strategy_agent import THREAT_INDICATORS
from src.models import (
    AlertLevel,
    IndicatorType,
    SocialPost,
    ThreatAssessment,
    ThreatIndicator,
)

logger = logging.getLogger(__name__)

# Pesos por categoría de indicador (suma máxima: 1.0 si todos activan)
INDICATOR_WEIGHTS: dict[str, float] = {
    "amenaza_directa": 0.40,
    "coordinacion_ataque": 0.30,
    "llamada_violencia": 0.20,
    "glorificacion_terrorismo": 0.15,
    "reclutamiento": 0.10,
}


def _score_to_level(score: float) -> AlertLevel:
    """Convierte un risk_score numérico al nivel de alerta correspondiente."""
    if score >= 0.75:
        return AlertLevel.ROJO
    if score >= 0.50:
        return AlertLevel.NARANJA
    if score >= 0.30:
        return AlertLevel.AMARILLO
    return AlertLevel.VERDE


def analyze_post(post: SocialPost) -> ThreatAssessment:
    """
    Analiza una publicación pública en busca de indicadores de amenaza.

    Args:
        post: Publicación pública a analizar.

    Returns:
        ThreatAssessment con indicadores encontrados, risk_score y nivel de alerta.
    """
    logger.debug("ANALYSIS_AGENT: analizando post %s de %s", post.id, post.platform)

    content_lower = post.content.lower()
    found_indicators: list[ThreatIndicator] = []
    accumulated_score = 0.0

    for category, patterns in THREAT_INDICATORS.items():
        category_weight = INDICATOR_WEIGHTS.get(category, 0.05)
        category_matched = False

        for pattern in patterns:
            try:
                match = re.search(pattern, content_lower, re.IGNORECASE)
                if match:
                    matched_text = match.group(0)
                    confidence = min(1.0, 0.6 + (0.1 * len(matched_text.split())))

                    indicator = ThreatIndicator(
                        type=IndicatorType(category),
                        value=matched_text,
                        explanation=_build_explanation(category, matched_text),
                        confidence=confidence,
                    )
                    found_indicators.append(indicator)

                    if not category_matched:
                        accumulated_score += category_weight * confidence
                        category_matched = True

            except re.error as e:
                logger.warning("ANALYSIS_AGENT: regex inválido '%s': %s", pattern, e)

    # Bonus por múltiples categorías distintas (señal más fuerte)
    categories_hit = len({ind.type for ind in found_indicators})
    if categories_hit >= 2:
        accumulated_score = min(1.0, accumulated_score * 1.2)
    if categories_hit >= 3:
        accumulated_score = min(1.0, accumulated_score * 1.3)

    risk_score = round(min(1.0, accumulated_score), 4)
    alert_level = _score_to_level(risk_score)
    requires_review = alert_level != AlertLevel.VERDE

    assessment = ThreatAssessment(
        id=str(uuid.uuid4()),
        post_id=post.id,
        indicators_found=found_indicators,
        risk_score=risk_score,
        alert_level=alert_level,
        requires_human_review=requires_review,
        assessment_timestamp=datetime.now(timezone.utc),
    )

    logger.info(
        "ANALYSIS_AGENT: post %s → score=%.4f nivel=%s indicadores=%d",
        post.id,
        risk_score,
        alert_level,
        len(found_indicators),
    )
    return assessment


def _build_explanation(category: str, matched_text: str) -> str:
    """Genera una explicación legible para el analista sobre el indicador detectado."""
    explanations = {
        "llamada_violencia": f"Llamada explícita a la violencia: '{matched_text}'",
        "coordinacion_ataque": f"Posible coordinación de acción violenta: '{matched_text}'",
        "glorificacion_terrorismo": f"Glorificación de actos terroristas: '{matched_text}'",
        "reclutamiento": f"Patrón de reclutamiento para actividad violenta: '{matched_text}'",
        "amenaza_directa": f"Amenaza directa e identificable: '{matched_text}'",
    }
    return explanations.get(category, f"Indicador de categoría '{category}': '{matched_text}'")
