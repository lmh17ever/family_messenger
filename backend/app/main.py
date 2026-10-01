from contextlib import asynccontextmanager

import uvicorn
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from timing_asgi import TimingMiddleware
from timing_asgi.integrations import StarletteScopeToName

from app.api.routes.router import v1_router
from app.core.config import settings
from app.core.logging import LogTimings, setup_logging
from app.core.realtime.websocket_manager import websocket_manager


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        setup_logging()
        yield
    finally:
        await websocket_manager.close()

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
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    TimingMiddleware,
    client=LogTimings(),
    metric_namer=StarletteScopeToName(prefix="myapp", starlette_app=app)
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
        limit_concurrency=settings.LIMIT_CONCURRENCY,
    )
