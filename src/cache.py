"""
Gestión de caché y rate limiting con Redis.
Soporte para alta disponibilidad y escalabilidad.
"""
import os
import time
import json
import logging
from typing import Optional, Any

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Configuración de Redis
# ─────────────────────────────────────────────────────────────────────────────
REDIS_URL = os.environ.get("REDIS_URL", None)
if REDIS_URL is None:
    if os.environ.get("VIGIA_ENV", "development").lower() == "production":
        raise RuntimeError("REDIS_URL no está definida. Es obligatoria en producción.")
    REDIS_URL = "redis://localhost:6379"

# Pool de conexiones global
redis_pool: aioredis.ConnectionPool | None = None


async def get_redis() -> aioredis.Redis:
    """Obtiene una conexión Redis del pool."""
    global redis_pool
    if redis_pool is None:
        redis_pool = aioredis.ConnectionPool.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
        )
    return aioredis.Redis(connection_pool=redis_pool)


async def close_redis() -> None:
    """Cierra el pool de conexiones Redis."""
    global redis_pool
    if redis_pool:
        await redis_pool.disconnect()
        redis_pool = None


# ─────────────────────────────────────────────────────────────────────────────
# Rate Limiting (Sliding Window Counter)
# ─────────────────────────────────────────────────────────────────────────────
async def check_rate_limit(
    identifier: str,
    max_requests: int = 100,
    window_seconds: int = 60,
) -> tuple[bool, dict]:
    """
    Verifica rate limiting usando sliding window.
    Devuelve: (allowed, info_dict)
    """
    redis = await get_redis()
    now = time.monotonic()
    window_start = now - window_seconds

    key = f"ratelimit:{identifier}"

    # Sliding window usando sorted set
    pipe = redis.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)  # Limpiar entradas antiguas
    pipe.zadd(key, {str(now): now})  # Añadir petición actual
    pipe.zcard(key)  # Contar peticiones en ventana
    pipe.expire(key, window_seconds)  # TTL para limpieza

    results = await pipe.execute()
    current_count = results[2]

    allowed = current_count <= max_requests
    info = {
        "limit": max_requests,
        "remaining": max(0, max_requests - current_count),
        "reset": window_seconds,
        "current": current_count,
    }

    return allowed, info


# ─────────────────────────────────────────────────────────────────────────────
# Caché con Redis
# ─────────────────────────────────────────────────────────────────────────────
async def cache_get(key: str) -> Any | None:
    """Obtiene un valor de la caché."""
    redis = await get_redis()
    value = await redis.get(f"cache:{key}")
    if value:
        return json.loads(value)
    return None


async def cache_set(key: str, value: Any, ttl_seconds: int = 300) -> None:
    """Almacena un valor en la caché con TTL."""
    redis = await get_redis()
    await redis.setex(
        f"cache:{key}",
        ttl_seconds,
        json.dumps(value, default=str),
    )


async def cache_delete(key: str) -> None:
    """Elimina un valor de la caché."""
    redis = await get_redis()
    await redis.delete(f"cache:{key}")


async def cache_clear_pattern(pattern: str) -> None:
    """Elimina todas las claves que coincidan con un patrón."""
    redis = await get_redis()
    cursor = 0
    full_pattern = f"cache:{pattern}"
    while True:
        cursor, keys = await redis.scan(cursor=cursor, match=full_pattern, count=100)
        if keys:
            await redis.delete(*keys)
        if cursor == 0:
            break


# ─────────────────────────────────────────────────────────────────────────────
# Colas de mensajes (para procesamiento asíncrono)
# ─────────────────────────────────────────────────────────────────────────────
async def queue_push(queue_name: str, message: dict) -> None:
    """Añade un mensaje a una cola (Lista Redis)."""
    redis = await get_redis()
    await redis.rpush(f"queue:{queue_name}", json.dumps(message))


async def queue_pop(queue_name: str, timeout: int = 0) -> dict | None:
    """Extrae un mensaje de una cola (bloqueante opcional)."""
    redis = await get_redis()
    if timeout > 0:
        result = await redis.blpop(f"queue:{queue_name}", timeout=timeout)
        if result:
            return json.loads(result[1])
    else:
        result = await redis.lpop(f"queue:{queue_name}")
        if result:
            return json.loads(result)
    return None


async def queue_length(queue_name: str) -> int:
    """Obtiene la longitud de una cola."""
    redis = await get_redis()
    return await redis.llen(f"queue:{queue_name}")


# ─────────────────────────────────────────────────────────────────────────────
# Locks distribuidos (para concurrencia)
# ─────────────────────────────────────────────────────────────────────────────
async def acquire_lock(lock_name: str, timeout: int = 10) -> bool:
    """Adquiere un lock distribuido."""
    redis = await get_redis()
    identifier = str(time.monotonic())
    result = await redis.set(
        f"lock:{lock_name}",
        identifier,
        nx=True,
        ex=timeout,
    )
    return bool(result)


async def release_lock(lock_name: str) -> None:
    """Libera un lock distribuido."""
    redis = await get_redis()
    await redis.delete(f"lock:{lock_name}")


# ─────────────────────────────────────────────────────────────────────────────
# Gestión de refresh tokens (revocación + rotación)
# ─────────────────────────────────────────────────────────────────────────────
def _refresh_jti_key(jti: str) -> str:
    return f"refresh_jti:{jti}"


def _refresh_user_key(analyst_id: str) -> str:
    return f"refresh_user:{analyst_id}"


async def register_refresh_jti(jti: str, analyst_id: str, ttl_seconds: int) -> None:
    """Registra un refresh token jti en Redis con TTL y lo añade al set del analista."""
    redis = await get_redis()
    pipe = redis.pipeline()
    pipe.setex(_refresh_jti_key(jti), ttl_seconds, analyst_id)
    pipe.sadd(_refresh_user_key(analyst_id), jti)
    pipe.expire(_refresh_user_key(analyst_id), ttl_seconds)
    await pipe.execute()


async def is_refresh_jti_valid(jti: str) -> Optional[str]:
    """
    Verifica si un jti es válido. Devuelve el analyst_id si lo es, None si no.
    """
    redis = await get_redis()
    return await redis.get(_refresh_jti_key(jti))


async def revoke_refresh_jti(jti: str, analyst_id: Optional[str] = None) -> None:
    """Revoca un refresh token concreto y lo elimina del set del analista."""
    redis = await get_redis()
    pipe = redis.pipeline()
    pipe.delete(_refresh_jti_key(jti))
    if analyst_id:
        pipe.srem(_refresh_user_key(analyst_id), jti)
    await pipe.execute()


async def revoke_all_refresh_for_user(analyst_id: str) -> int:
    """Revoca todos los refresh tokens del analista. Devuelve cantidad revocada."""
    redis = await get_redis()
    user_key = _refresh_user_key(analyst_id)
    jtis = await redis.smembers(user_key)
    if not jtis:
        return 0
    pipe = redis.pipeline()
    for jti in jtis:
        pipe.delete(_refresh_jti_key(jti))
    pipe.delete(user_key)
    await pipe.execute()
    return len(jtis)
