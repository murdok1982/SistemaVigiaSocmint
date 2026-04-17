"""
RESEARCH_AGENT — Simula la recopilación de contenido público en redes sociales.

En producción, este agente usaría APIs oficiales (Twitter API v2, Reddit API, etc.)
con credenciales propias del organismo. En esta versión de prototipo genera
datos de muestra para demostrar el flujo completo del sistema.

IMPORTANTE: Solo fuentes públicas. Nunca autentica como tercero.
"""
import hashlib
import logging
import uuid
from datetime import datetime, timezone

from src.models import SocialPost

logger = logging.getLogger(__name__)


def _hash_author_id(raw_id: str) -> str:
    """Hashea el author_id para anonimización antes de almacenar."""
    return hashlib.sha256(raw_id.encode()).hexdigest()[:16]


def _make_sample_posts() -> list[SocialPost]:
    """
    Genera publicaciones de muestra para el prototipo.
    En producción, este método sería reemplazado por llamadas a APIs reales.
    """
    now = datetime.now(timezone.utc)
    samples = [
        SocialPost(
            id=str(uuid.uuid4()),
            platform="twitter",
            content="Hay que destruir el sistema, no podemos seguir así. El cambio viene por la fuerza.",
            author_id_hash=_hash_author_id("user_tw_001"),
            timestamp=now,
            url="https://twitter.com/[anonimizado]/status/[id]",
            is_public=True,
            language="es",
        ),
        SocialPost(
            id=str(uuid.uuid4()),
            platform="telegram",
            content="Coordinar el ataque el próximo viernes. Punto de encuentro: ya sabéis dónde.",
            author_id_hash=_hash_author_id("user_tg_002"),
            timestamp=now,
            url="https://t.me/[canal_publico]/[id]",
            is_public=True,
            language="es",
        ),
        SocialPost(
            id=str(uuid.uuid4()),
            platform="reddit",
            content="Estoy harto de todo esto. A veces pienso que la única solución es la radical.",
            author_id_hash=_hash_author_id("user_rd_003"),
            timestamp=now,
            url="https://reddit.com/r/[sub]/comments/[id]",
            is_public=True,
            language="es",
        ),
        SocialPost(
            id=str(uuid.uuid4()),
            platform="twitter",
            content="La situación política actual es preocupante. Necesitamos debate y cambio democrático.",
            author_id_hash=_hash_author_id("user_tw_004"),
            timestamp=now,
            url="https://twitter.com/[anonimizado]/status/[id]",
            is_public=True,
            language="es",
        ),
        SocialPost(
            id=str(uuid.uuid4()),
            platform="facebook",
            content="Voy a mataros a todos si no cambian las cosas. Estoy al límite.",
            author_id_hash=_hash_author_id("user_fb_005"),
            timestamp=now,
            url="https://facebook.com/[page]/posts/[id]",
            is_public=True,
            language="es",
        ),
    ]
    return samples


async def collect_public_content(
    platforms: list[str],
    keywords: list[str],
    max_results: int = 100,
) -> list[SocialPost]:
    """
    Recopila contenido público de las plataformas especificadas.

    Args:
        platforms: Lista de plataformas a monitorear.
        keywords: Palabras clave a buscar (usadas en APIs reales).
        max_results: Límite máximo de resultados por plataforma.

    Returns:
        Lista de SocialPost con contenido público recopilado.
    """
    logger.info(
        "RESEARCH_AGENT: recopilando contenido de %s plataformas (máx %d resultados)",
        len(platforms),
        max_results,
    )

    # Prototipo: devuelve datos de muestra
    # En producción: llamar a APIs oficiales con credenciales del organismo
    posts = _make_sample_posts()

    # Filtrar solo plataformas solicitadas
    filtered = [p for p in posts if p.platform in platforms] if platforms else posts

    logger.info("RESEARCH_AGENT: %d posts recopilados (prototipo)", len(filtered))
    return filtered[:max_results]
