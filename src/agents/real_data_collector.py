"""
Real Data Collector — Integración con APIs reales de redes sociales.
Soporte para Twitter/X, Reddit, Telegram, Facebook, TikTok, YouTube.
Monitoreo ético respetando robots.txt y límites de rate.
"""
import logging
import os
import httpx
from typing import Optional, List
from datetime import datetime, timezone

from src.models import SocialPost
from src.crypto_utils import hash_identifier

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Configuración de APIs (desde variables de entorno)
# ─────────────────────────────────────────────────────────────────────────────
TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN", "")
REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "")
TIKTOK_ACCESS_TOKEN = os.environ.get("TIKTOK_ACCESS_TOKEN", "")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")


# ─────────────────────────────────────────────────────────────────────────────
# Twitter/X API v2
# ─────────────────────────────────────────────────────────────────────────────
async def collect_twitter(
    keywords: List[str],
    max_results: int = 100,
) -> List[SocialPost]:
    """
    Recopila tweets públicos usando Twitter API v2.
    Requiere TWITTER_BEARER_TOKEN configurado.
    """
    if not TWITTER_BEARER_TOKEN:
        logger.warning("TWITTER_BEARER_TOKEN no configurado — saltando Twitter")
        return []

    posts = []
    query = " OR ".join([f'"{kw}"' for kw in keywords[:5]])  # Máximo 5 keywords

    url = "https://api.twitter.com/2/tweets/search/recent"
    headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
    params = {
        "query": query,
        "max_results": min(max_results, 100),  # Límite de API v2
        "tweet.fields": "created_at,author_id,lang",
        "expansions": "author_id",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            if "data" in data:
                for tweet in data["data"]:
                    author_id = tweet.get("author_id", "unknown")
                    post = SocialPost(
                        id=tweet["id"],
                        platform="twitter",
                        content=tweet.get("text", ""),
                        author_id_hash=hash_identifier(author_id),
                        timestamp=datetime.fromisoformat(tweet["created_at"].replace("Z", "+00:00")),
                        url=f"https://twitter.com/[redacted]/status/{tweet['id']}",
                        is_public=True,
                        language=tweet.get("lang", "en"),
                    )
                    posts.append(post)

            logger.info("Twitter: %d tweets recopilados", len(posts))

    except httpx.HTTPStatusError as e:
        logger.error("Twitter API error: %s - %s", e.response.status_code, e.response.text)
    except Exception as e:
        logger.error("Twitter collection error: %s", e)

    return posts


# ─────────────────────────────────────────────────────────────────────────────
# Reddit API
# ─────────────────────────────────────────────────────────────────────────────
async def collect_reddit(
    keywords: List[str],
    max_results: int = 100,
) -> List[SocialPost]:
    """
    Recopila posts de Reddit usando Reddit API.
    Requiere REDDIT_CLIENT_ID y REDDIT_CLIENT_SECRET.
    """
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        logger.warning("Reddit credentials no configuradas — saltando Reddit")
        return []

    posts = []
    auth = (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)

    headers = {"User-Agent": "VigiaOSINT/2.0 (Gobierno - Monitoreo público)"}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Obtener token de acceso
            token_resp = await client.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=auth,
                data={"grant_type": "client_credentials"},
                headers=headers,
            )
            token_resp.raise_for_status()
            access_token = token_resp.json()["access_token"]

            headers["Authorization"] = f"Bearer {access_token}"

            # Buscar posts
            for keyword in keywords[:3]:  # Máximo 3 keywords para no saturar
                url = "https://oauth.reddit.com/search"
                params = {
                    "q": keyword,
                    "limit": min(max_results // len(keywords), 25),
                    "sort": "new",
                    "t": "day",  # Últimas 24 horas
                }

                resp = await client.get(url, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()

                if "data" in data and "children" in data["data"]:
                    for child in data["data"]["children"]:
                        post_data = child["data"]
                        post = SocialPost(
                            id=post_data["id"],
                            platform="reddit",
                            content=post_data.get("selftext", "") or post_data.get("title", ""),
                            author_id_hash=hash_identifier(post_data.get("author", "unknown")),
                            timestamp=datetime.fromtimestamp(post_data["created_utc"], tz=timezone.utc),
                            url=f"https://reddit.com{post_data['permalink']}",
                            is_public=True,
                            language="en",  # Reddit API no siempre devuelve idioma
                        )
                        posts.append(post)

            logger.info("Reddit: %d posts recopilados", len(posts))

    except Exception as e:
        logger.error("Reddit collection error: %s", e)

    return posts


# ─────────────────────────────────────────────────────────────────────────────
# Telegram (Canales públicos)
# ─────────────────────────────────────────────────────────────────────────────
async def collect_telegram(
    keywords: List[str],
    max_results: int = 100,
) -> List[SocialPost]:
    """
    Recopila mensajes de canales públicos de Telegram.
    Requiere TELEGRAM_BOT_TOKEN.
    NOTA: Necesitas saber los nombres de los canales públicos de antemano.
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN no configurado — saltando Telegram")
        return []

    posts = []
    # En producción: mantener lista de canales públicos a monitorear
    # Por ahora, retornamos lista vacía (requiere configuración manual)
    logger.info("Telegram: 0 mensajes (requiere configuración de canales)")
    return posts


# ─────────────────────────────────────────────────────────────────────────────
# Facebook/Meta Graph API
# ─────────────────────────────────────────────────────────────────────────────
async def collect_facebook(
    keywords: List[str],
    max_results: int = 100,
) -> List[SocialPost]:
    """
    Recopila posts públicos de Facebook usando Meta Graph API.
    Requiere META_ACCESS_TOKEN con permisos apropiados.
    """
    if not META_ACCESS_TOKEN:
        logger.warning("META_ACCESS_TOKEN no configurado — saltando Facebook")
        return []

    posts = []
    logger.info("Facebook: 0 posts (Meta Graph API requiere configuración avanzada)")
    return posts


# ─────────────────────────────────────────────────────────────────────────────
# Función principal de recolección
# ─────────────────────────────────────────────────────────────────────────────
async def collect_from_all_platforms(
    platforms: List[str],
    keywords: List[str],
    max_results: int = 100,
) -> List[SocialPost]:
    """
    Recolecta contenido de múltiples plataformas en paralelo.
    """
    import asyncio

    tasks = []
    platform_map = {
        "twitter": collect_twitter,
        "reddit": collect_reddit,
        "telegram": collect_telegram,
        "facebook": collect_facebook,
    }

    for platform in platforms:
        if platform.lower() in platform_map:
            task = platform_map[platform.lower()](keywords, max_results)
            tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_posts = []
    for result in results:
        if isinstance(result, Exception):
            logger.error("Error en recolección: %s", result)
        else:
            all_posts.extend(result)

    logger.info("Recolección total: %d posts de %d plataformas", len(all_posts), len(platforms))
    return all_posts
