# Family Messenger

Локальный мессенджер для семьи: прямые и групповые (пока только на бекенде) чаты, файлы/аватарки в S3, веб-сокеты для реального времени.

- **Бэкенд:** FastAPI (Python 3.14) + PostgreSQL (asyncpg) + Redis (pub/sub)
- **Фронтенд:** SvelteKit + Tailwind CSS, собирается в статику и отдаётся nginx
- **Репозиторий:** `lmh17ever/family_messenger`

> Основной README для разработки в репозитории. Для серверной части есть также
> `backend/README.md` (если он будет создан).

---

## Содержание

## Возможности

- Регистрация и вход по JWT (access + refresh)
- Прямые чаты и создание групповых чатов
- Отправка текстовых сообщений через REST и веб-сокеты
- Загрузка вложений (presigned POST в S3) и презентация по защищённому URL
- Загрузка/изменение аватарок пользователей и групповых чатов
- Чтение сообщений, подсчёт непрочитанных, пометка чата как прочитанного
- Поиск сообщений (PostgreSQL `gin_trgm`)
- Реальное время через Redis pub/sub и `websockets`
- Безопасность:
  - токены в URL веб-сокета маскируются в логах (фильтр `SecretsMaskingFilter`);
  - валидация mime-типов, размеров файлов;
  - пресеты S3 с ограничением диапазона `content-length-range`.

## Архитектура

```text
client (browser)
   |  HTTPS (nginx:80/443)
   v
frontend (SvelteKit, статика + nginx)
   |  REST + WS
   v
backend (FastAPI:8000)
   |  SQLAlchemy asyncpg
   v
PostgreSQL 16  <-- сообщения, чаты, пользователи, вложения
   |
   +-- Redis pub/sub  <-- broadcast сообщений/уведомлений
   |
   +-- S3 (private и public bucket)
```
## Структура проекта

```text
family_messenger/
├── backend/                  # FastAPI-сервер
│   ├── app/
│   │   ├── api/
│   │   │   ├── dependencies/ # get_session, get_current_user, get_chat_as_member, get_websocket_user
│   │   │   └── routes/
│   │   │       ├── router.py          # /api/v1, подключение всех роутов
│   │   │       ├── endpoints/
│   │   │           ├── auth.py        # register, login, refresh
│   │   │           ├── chat.py        # чаты, участники, аватарки чатов
│   │   │           ├── message.py     # создание, чтение, редактирование, удаление
│   │   │           ├── attachment.py  # presign, download url, confirm
│   │   │           ├── user.py        # профиль, аватарка пользователя
│   │   │           └── websocket.py   # chat ws и user ws
│   │   ├── core/
│   │   │   ├── config.py              # Settings (pydantic-settings)
│   │   │   ├── database.py            # async engine + session
│   │   │   ├── logging.py             # JSON-логи, маскировка секретов
│   │   │   ├── realtime/              # WebSocketManager, RedisManager
│   │   │   ├── security.py            # password hash, JWT, current user
│   │   │   └── storage.py             # S3 client, presign_get/post, delete
│   │   ├── crud/                      # операции с БД (user, chat, message, attachment)
│   │   ├── models/                    # SQLAlchemy models: User, Chat, ChatMember, Message, Attachment
│   │   ├── schemas/                   # Pydantic v2 схемы
│   │   ├── services/                  # business logic: user, chat, message, attachments, avatars, realtime
│   │   ├── db/base.py
│   │   ├── main.py                    # FastAPI app, lifespan, middleware
│   │   └── alembic/                   # миграции
## Требования

- Windows / Linux / macOS
- Docker + Docker Compose (для полного стека)
- Для локальной разработки:
  - Python 3.14+ (виртуальное окружение, рекомендуется `uv`)
  - Node.js 20+ (для фронтенда)
  - PostgreSQL 16
  - Redis 7

## Быстрый старт

### 1. Клонирование и переменные окружения

```bash
git clone git@github.com:lmh17ever/family_messenger.git
cd family_messenger
cp backend/.env.example backend/.env       # если файл есть
cp frontend/.env.example frontend/.env     # если файл есть
```


### 2. Локальный стек (Docker Compose)

```bash
docker compose up --build -d
```

Запустит:

- `web` — фронтенд на порту `80/443` через nginx
- `backend` — FastAPI на `http://localhost:8000`
- `db` — PostgreSQL 16
- `redis` — Redis 7
- `nginx` — веб-сервер с SSL-терминалом (если настроены сертификаты)

### 3. Тесты (только backend)

```bash
cd backend
python -m pytest -q
```

## Переменные окружения

```dotenv
# Database (Docker: host = db; local dev: host = localhost)
DB_USER=user
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=messenger

# Security
JWT_ACCESS_SECRET_KEY=...
JWT_REFRESH_SECRET_KEY=...
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# CORS
ALLOW_ORIGINS=['0.0.0.0', 'http://localhost', 'http://localhost:5173', 'http://localhost:3000']
ALLOW_CREDENTIALS=true
ALLOW_METHODS=['*']
ALLOW_HEADERS=['*']

### `backend/.env`

```dotenv
# Database (Docker: host = db; local dev: host = localhost)
DB_USER=user
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=messenger

# Security
JWT_ACCESS_SECRET_KEY=...
JWT_REFRESH_SECRET_KEY=...
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# CORS
ALLOW_ORIGINS=['0.0.0.0', 'http://localhost', 'http://localhost:5173', 'http://localhost:3000']
ALLOW_CREDENTIALS=true
ALLOW_METHODS=['*']
ALLOW_HEADERS=['*']
```

### `frontend/.env`

```dotenv
# Базовый URL backend без /api/v1 (добавляется в src/lib/config.ts)
# В Docker используйте домен/localhost, не http://backend:8000
VITE_API_BASE_URL=http://localhost

PUBLIC_S3_BASE_URL=https://storage.clo.ru
PUBLIC_S3_PUBLIC_BUCKET=messenger-public-bucket
```

### `docker-compose.yml` (переменные для контейнеров)

- `VITE_API_BASE_URL` — передаётся в Dockerfile фронтенда при сборке.
- `PUBLIC_S3_BASE_URL` и `PUBLIC_S3_PUBLIC_BUCKET` — для S3-ссылок в фронтенде.
- `DB_USER`, `DB_PASSWORD`, `DB_NAME` — используются и для postgres, и для `DATABASE_URL` backend.

Обновлённая документация доступна по адресам:

- `GET  /api/v1/health` — health check
- `GET  /api/v1/docs` — Swagger UI
- `GET  /api/v1/redoc` — ReDoc (только если `DEBUG=true`)

### Регистрация и вход

- `POST /api/v1/auth/register` — регистрация; возвращает `access_token` + `refresh_token`
- `POST /api/v1/auth/token` — логин (OAuth2 `username`/`password`)
- `POST /api/v1/auth/token/refresh` — обновление access-токена

### Пользователи

- `GET /api/v1/users/me` — текущий пользователь
- `PATCH /api/v1/users/me` — смена username
- `POST /api/v1/users/me/avatar/presign` — presign для avatar
- `POST /api/v1/users/me/avatar/confirm` — подтверждение avatar
- `GET /api/v1/users` — список пользователей (поле `avatar_url`)
- `GET /api/v1/users/{user_id}` — пользователь
- `DELETE /api/v1/users/{user_id}` — удаление (только сам пользователь или суперпользователь)

### Чаты

- `POST /api/v1/chats/{user_id}` — открыть/получить уже существующий прямым чатом
- `POST /api/v1/chats` — создать групповой чат (payload: `title`, `member_ids`)
- `GET /api/v1/chats/my` — список чатов текущего пользователя
- `GET /api/v1/chats/{chat_id}` — подробности чата (с участниками и последним сообщением)
- `POST /api/v1/chats/{chat_id}/read` — пометить сообщение как прочитанное
- `POST /api/v1/chats/{chat_id}/avatar/presign` — avtar presign для чата
- `POST /api/v1/chats/{chat_id}/avatar/confirm` — подтверждение аватарки чата
- `POST /api/v1/chats/{chat_id}/members` — добавить участника (только создатель)
- `DELETE /api/v1/chats/{chat_id}/members/{user_id}` — удалить участника
- `DELETE /api/v1/chats/{chat_id}` — удалить чат

### Сообщения

- `POST /api/v1/chats/{chat_id}/messages` — отправить сообщение
- `GET /api/v1/chats/{chat_id}/messages` — список (пагинация `before_id`, `limit`, `search`)
## Веб-сокеты

- `ws://host/api/v1/chats/{chat_id}/ws?token=<access_token>`
  - события: `connected`, `message.created`, `message.updated`, `chat.updated`, `notification.new_message`, `ping`/`pong`
  - отправляется `{"type": "send_message", "message": {...}}`
- `ws://host/api/v1/users/me/ws?token=<access_token>`
  - события: `connected`, `chat.updated` (уведомление о изменении чата пользователя)

> Токен в query-параметре веб-сокета маскируется в логах (см. `backend/app/core/logging.py`).

## База данных и миграции

- Движок: SQLAlchemy async + `asyncpg`.
- Модели: `User`, `Chat`, `ChatMember`, `Message`, `Attachment`.
- Миграции лежат в `backend/alembic/versions`.
- При сборке в Docker миграции запускаются через `alembic upgrade head`.
- Схемы инициализируются из `backend/app/db/base.py` (названия ограничений с префиксами `ix_`, `uq_`, `fk_`, `ck_`).

## Логирование

- JSON-логи на stdout и `logs/app.log.jsonl` (при `DEBUG=true`).
- `SecretsMaskingFilter` маскирует `token=` в сообщениях логов.
- Уровни: `uvicorn` и `sqlalchemy.engine` — `WARNING`, корневой `DEBUG`.

## Docker развёртывание

```bash
docker compose build
docker compose up -d
```

- `backend`.healthcheck: `/api/v1/health` должен отвечать `200`.
- `web` отдаёт фронтенд и настроен через `nginx.conf`.
- Контейнер `backend` автоматически запускает `alembic upgrade head` при старте.

## Локальная разработка

## Тесты

```bash
cd backend
python -m pytest -q
```

Включает тесты на:

- регистрацию, логин, refresh
- чаты, участники, аватарки
- сообщения (CRUD, пагинацию, поиск)
- вложения (presign, конфирмация)
- веб-сокеты (broadcast, валидацию, HTTP-сообщение в WS)
- health check

## Прочее

- Планируемые фичи (по `plan.md`): блокировка пользователя, управление приглашениями в группах, регистрация по секретному токену.
- Баг-фиксы и улучшения, отмеченные в `plan.md`:
  - обработка ошибок при удалении объектов S3 (не ломать удаление остальных ключей);
  - покрытие `isort`/`black`/`ruff`;
  - дальнейшее изучение SQLAlchemy;
  - индексы для `chat_member.last_read_message_id` и `chat.last_message_id`.

## Примечание по `plan.md`

Файл `plan.md` в корне — это рабочий чек-лист и технические заметки, а не готовая документация. В README приведены актуальные команды и конфигурации из репозитория.

## Лицензия

См. файл `LICENSE`.



### Backend

```bash
cd backend
python -m venv .venv
# или: uv venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"     # или: uv sync --dev
python -m app.main
```

Порт: `8000` (конфигурируется через `UVICORN_HOST`/`UVICORN_PORT`).

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Сборка:

```bash
npm run build
npm run preview
```


- `PATCH /api/v1/chats/{chat_id}/messages/{message_id}` — редактировать текст
- `DELETE /api/v1/chats/{chat_id}/messages/{message_id}` — удалить (только автор)

### Вложения

- `POST /api/v1/chats/{chat_id}/attachments/presign` — получить presigned POST для загрузки файла
- `GET /api/v1/attachments/{attachment_id}/url` — презент по upload URL
- `POST /api/v1/attachments/{attachment_id}/confirm` — подтверждение размера/типа после загрузки



# S3
S3_ENDPOINT=https://storage.clo.ru
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
S3_PRIVATE_BUCKET=messenger-private-bucket
S3_PUBLIC_BUCKET=messenger-public-bucket
S3_BASE_URL=https://storage.clo.ru

MAX_AVATAR_SIZE=20        # 20 MB
MAX_ATTACHMENT_SIZE=500   # 500 MB
```

### `frontend/.env`

```dotenv
# Базовый URL backend без /api/v1 (добавляется в src/lib/config.ts)
# В Docker используйте домен/localhost, не http://backend:8000
VITE_API_BASE_URL=http://localhost

PUBLIC_S3_BASE_URL=https://storage.clo.ru
PUBLIC_S3_PUBLIC_BUCKET=messenger-public-bucket
```

### `docker-compose.yml` (переменные для контейнеров)

- `VITE_API_BASE_URL` — передаётся в Dockerfile фронтенда при сборке.
- `PUBLIC_S3_BASE_URL` и `PUBLIC_S3_PUBLIC_BUCKET` — для S3-ссылок в фронтенде.
- `DB_USER`, `DB_PASSWORD`, `DB_NAME` — используются и для postgres, и для `DATABASE_URL` backend.


python -m pytest -q
```


│   ├── .env                           # переменные окружения (не коммитить)
│   ├── pyproject.toml
│   └── tests/                         # pytest-тесты (вкл. websocket)
├── frontend/                          # SvelteKit + Tailwind
│   ├── src/
│   │   ├── lib/config.ts              # единая точка конфигурации (API_URL, WS_URL, S3...)
│   │   ├── routes/                    # SvelteKit routes
│   │   └── app.css
│   ├── nginx.conf
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
├── nginx/
├── plan.md                            # технические задачи / будущие фичи
├── LICENSE
└── README.md




- `backend`: API, бизнес-логика, взаимодействие с БД и S3, WebSocket-компоненты.
- `frontend`: SPA, `Vite`/`SvelteKit`, прокси/апи-базовые URL конфигурируются переменными.
- `nginx`: фронтенд статику отдаёт, базовый путь API можно настроить через `nginx.conf`.
- `docker-compose`: PostgreSQL 16, Redis 7, backend и фронтенд в отдельных контейнерах.



1. [Возможности](#возможности)
2. [Архитектура](#архитектура)
3. [Структура проекта](#структура-проекта)
4. [Требования](#требования)
5. [Быстрый старт](#быстрый-старт)
6. [Переменные окружения](#переменные-окружения)
7. [Документация API](#документация-api)
8. [Веб-сокеты](#веб-сокеты)
9. [База данных и миграции](#база-данных-и-миграции)
10. [Логирование](#логирование)
11. [Docker развёртывание](#docker-развёртывание)
12. [Локальная разработка](#локальная-разработка)
13. [Тесты](#тесты)
14. [Прочее](#прочее)
15. [Примечание по `plan.md`](#примечание-по-plangmd)
16. [Лицензия](#лицензия)
