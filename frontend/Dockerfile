# ── Stage 1: build the SPA ──────────────────────────────────────────────
FROM node:22-slim AS builder

WORKDIR /app

# Переменные для билда (публичные, они встраиваются в бандл)
ARG VITE_API_BASE_URL
ARG PUBLIC_S3_BASE_URL
ARG PUBLIC_S3_PUBLIC_BUCKET
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV PUBLIC_S3_BASE_URL=${PUBLIC_S3_BASE_URL}
ENV PUBLIC_S3_PUBLIC_BUCKET=${PUBLIC_S3_PUBLIC_BUCKET}

# Кэшируем слой с зависимостями
COPY package.json package-lock.json .npmrc ./
RUN npm ci --ignore-scripts

# Копируем исходники (без .env и .svelte-kit благодаря .dockerignore)
COPY . .

# Собираем статику (SPA) → /app/build/
RUN npm run build

# ── Stage 2: nginx serving the built SPA ────────────────────────────────
FROM nginx:stable-alpine AS runtime

# Копируем билд из builder-стадии
COPY --from=builder --chown=nginx:nginx /app/build /usr/share/nginx/html

# nginx config будет подмонтирован в docker-compose, но
# кладём дефолтный конфиг на случай, если монтировать забыли
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80 443
