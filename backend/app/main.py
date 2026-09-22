from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import uvicorn

from app.api.routes.router import v1_router
from app.core.config import settings

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=settings.ALLOW_CREDENTIALS,
    allow_methods=settings.ALLOW_METHODS,
    allow_headers=settings.ALLOW_HEADERS,
)

app.include_router(v1_router)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0")
