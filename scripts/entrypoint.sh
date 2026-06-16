#!/bin/sh
set -e

WORKERS="${WORKERS:-4}"
HOST="${API_HOST:-0.0.0.0}"
PORT="${API_PORT:-8000}"
LOG_LEVEL="${VIGIA_LOG_LEVEL:-info}"

echo "[entrypoint] VIGIA API starting (env=${VIGIA_ENV:-unknown})"

if [ "$VIGIA_ENV" = "production" ]; then
    echo "Running Alembic migrations..."
    if [ -f "/app/alembic.ini" ]; then
        alembic -c /app/alembic.ini upgrade head || echo "Migration warning (continuing...)"
    else
        echo "[entrypoint] WARN: /app/alembic.ini not found, skipping migrations"
    fi
fi

exec uvicorn src.api:app \
    --host "${HOST}" \
    --port "${PORT}" \
    --workers "${WORKERS}" \
    --log-level "${LOG_LEVEL}" \
    --proxy-headers \
    --forwarded-allow-ips='*'
