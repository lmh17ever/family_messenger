#!/usr/bin/env bash
set -e

echo "Waiting for PostgreSQL..."
until pg_isready -h db -U "${DB_USER:-user}" -d "${DB_NAME:-messenger}" >/dev/null 2>&1; do
  echo "PostgreSQL not ready, retrying in 2s..."
  sleep 2
done
echo "PostgreSQL is ready."

# Миграции
if [ -d "/app/alembic" ]; then
  echo "Running alembic migrations..."
  uv run alembic upgrade head
  echo "Migrations completed."
fi

exec uv run uvicorn app.main:app \
  --host "${UVICORN_HOST:-0.0.0.0}" \
  --port "${UVICORN_PORT:-8000}" \
  --workers "${UVICORN_WORKERS:-2}"
