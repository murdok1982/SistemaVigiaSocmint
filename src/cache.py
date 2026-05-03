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
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

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
    keys = await redis.keys(f"cache:{pattern}")
    if keys:
        await redis.delete(*keys)


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
