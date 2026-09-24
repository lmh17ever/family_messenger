from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import uvicorn

from app.api.routes.router import v1_router
from app.core.config import settings
from app.services.realtime import chat_connections


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        yield
    finally:
        await chat_connections.close()


app = FastAPI(
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=settings.ALLOW_CREDENTIALS,
    allow_methods=settings.ALLOW_METHODS,
    allow_headers=settings.ALLOW_HEADERS,
)

app.include_router(v1_router)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.UVICORN_HOST,
        port=settings.UVICORN_PORT,
        reload=settings.DEBUG,
        ws_max_size=settings.WS_MAX_SIZE,
        workers=settings.WORKERS,
        limit_concurrency=settings.LIMIT_CONCURRENCY
    )
