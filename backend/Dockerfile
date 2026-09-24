FROM python:3.14-slim

# Установка uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Установка клиентских утилит PostgreSQL (pg_isready нужен entrypoint.sh)
RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем файлы зависимостей и устанавливаем их
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev

# Копируем исходный код приложения
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

# Запускаем entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV UVICORN_WORKERS=2
ENV UVICORN_HOST=0.0.0.0
ENV UVICORN_PORT=8000

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
