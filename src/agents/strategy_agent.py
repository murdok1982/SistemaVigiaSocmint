"""
STRATEGY_AGENT — Define prioridades de monitoreo y keywords por plataforma.

Produce un plan de análisis estructurado con indicadores lingüísticos
específicos, sin categorías religiosas genéricas.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


# Indicadores lingüísticos organizados por categoría de amenaza.
# NOTA: estos indicadores se centran en llamadas a violencia y coordinación
# de acciones dañinas, NO en afiliación religiosa, política o étnica.
THREAT_INDICATORS: dict[str, list[str]] = {
    "llamada_violencia": [
        r"debemos atacar",
        r"hay que eliminar",
        r"matar a todos",
        r"destruir el",
        r"ejecutar el atentado",
        r"golpear el objetivo",
        r"liquidar a",
        r"aniquilar",
        r"masacrar",
    ],
    "coordinacion_ataque": [
        r"punto de encuentro",
        r"hora de la operación",
        r"el plan es",
        r"nos reunimos en",
        r"traed el material",
        r"coordinar el ataque",
        r"cuando llegue la señal",
        r"unidad de acción",
        r"ejecutar en simultáneo",
    ],
    "glorificacion_terrorismo": [
        r"martir",
        r"mártir glorioso",
        r"heroico atentado",
        r"operación exitosa",
        r"muertos merecidos",
        r"bien hecho el ataque",
        r"celebramos la acción",
        r"honor a los ejecutores",
    ],
    "reclutamiento": [
        r"únete a nosotros",
        r"necesitamos soldados",
        r"buscamos hermanos dispuestos",
        r"contacta si estás preparado",
        r"queremos gente comprometida",
        r"integra la célula",
        r"ven con nosotros",
    ],
    "amenaza_directa": [
        r"voy a matarte",
        r"te vamos a matar",
        r"pagarás con tu vida",
        r"hemos localizado tu",
        r"conocemos tu dirección",
        r"no sobrevivirás",
        r"eres el objetivo",
        r"atentado contra",
    ],
}

PLATFORM_STRATEGY = {
    "twitter": {
        "objective": "Monitoreo de menciones públicas con indicadores de amenaza",
        "content_types": ["tweets", "hilos", "respuestas públicas"],
        "api": "Twitter API v2 — Bearer Token, solo contenido público",
        "rate_limit_rpm": 450,
    },
    "telegram": {
        "objective": "Monitoreo de canales públicos indexados",
        "content_types": ["mensajes en canales públicos"],
        "api": "Telegram Bot API — solo canales públicos con enlace de invitación abierto",
        "rate_limit_rpm": 30,
    },
    "facebook": {
        "objective": "Monitoreo de publicaciones públicas en grupos abiertos",
        "content_types": ["posts públicos", "comentarios públicos"],
        "api": "Meta Graph API — solo contenido con visibilidad EVERYONE",
        "rate_limit_rpm": 200,
    },
    "reddit": {
        "objective": "Monitoreo de subreddits públicos con actividad sospechosa",
        "content_types": ["posts", "comentarios"],
        "api": "Reddit API — subs públicos, sin autenticación como usuario",
        "rate_limit_rpm": 60,
    },
    "web": {
        "objective": "Foros y chats públicos indexados",
        "content_types": ["foros abiertos", "chats públicos"],
        "api": "HTTP crawl respetando robots.txt",
        "rate_limit_rpm": 10,
    },
}


def build_strategy(objective: str) -> dict[str, Any]:
    """
    Genera un plan de monitoreo estructurado a partir del objetivo de análisis.

    Args:
        objective: Descripción del objetivo de análisis.

    Returns:
        Diccionario con la estrategia de monitoreo.
    """
    logger.info("STRATEGY_AGENT: construyendo plan para objetivo: %s", objective)

    kpis = [
        "tasa_falsos_positivos < 15%",
        "cobertura_plataformas >= 3",
        "tiempo_medio_deteccion < 30min",
        "alertas_ROJO revisadas en < 1h",
        "alertas_NARANJA revisadas en < 4h",
    ]

    return {
        "goal": objective,
        "channel_strategy": PLATFORM_STRATEGY,
        "threat_indicators": THREAT_INDICATORS,
        "priority_actions": [
            "Iniciar monitoreo de plataformas con API disponible (Twitter, Reddit)",
            "Configurar alertas automáticas para indicadores de nivel ROJO/NARANJA",
            "Establecer ciclo de revisión humana de 24h para alertas pendientes",
        ],
        "kpis": kpis,
        "audit_note": f"STRATEGY_AGENT: plan generado para objetivo '{objective}'",
    }
