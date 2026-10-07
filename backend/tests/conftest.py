"""Shared fixtures for integration tests.

!Requires local PostgreSQL and Redis!
Uses dedicated DB (messenger_test) and Redis DB 15 so developer data stays untouched.
Env overrides must be set before any app.* import because Settings is created at import time.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import Iterator
from unittest.mock import patch

# Must be set before importing anything from app
os.environ["DB_NAME"] = "messenger_test"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.api.dependencies.session import get_session
from app.core.config import settings
from app.db.base import Base
from app.models.user import User

# Ensure all models are registered
import app.models.attachment
import app.models.chat
import app.models.message
import app.models.user

from app.main import app as fastapi_app


test_engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
TestSession = async_sessionmaker(test_engine, autocommit=False, expire_on_commit=False)


async def _override_get_session():
    async with TestSession() as session:
        yield session


fastapi_app.dependency_overrides[get_session] = _override_get_session


def run_db(coro):
    return asyncio.run(coro)


async def _ensure_database() -> None:
    admin_url = (
        f"{settings.DB_ENGINE}://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/postgres"
    )
    admin_engine = create_async_engine(admin_url, poolclass=NullPool)
    try:
        async with admin_engine.connect() as conn:
            conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
            exists = await conn.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": settings.DB_NAME},
            )
            if not exists:
                await conn.execute(text(f"CREATE DATABASE {settings.DB_NAME}"))
    finally:
        await admin_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def database_schema() -> Iterator[None]:
    async def _setup() -> None:
        await _ensure_database()
        async with test_engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    run_db(_setup())
    yield
    run_db(test_engine.dispose())


@pytest.fixture(autouse=True)
def clean_state(database_schema: None) -> Iterator[None]:
    async def _truncate() -> None:
        tables = ", ".join(f'"{table.name}"' for table in Base.metadata.sorted_tables)
        async with test_engine.begin() as conn:
            await conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))

    run_db(_truncate())

    import redis as redis_sync

    redis_client = redis_sync.Redis.from_url(settings.REDIS_URL)
    try:
        redis_client.flushdb()
    finally:
        redis_client.close()

    yield


@pytest.fixture(autouse=True)
def s3_mock():
    with patch("app.core.storage.s3") as mock_s3:
        mock_s3.generate_presigned_post.return_value = {
            "url": "https://s3.example/upload",
            "fields": {"key": "placeholder"},
        }
        mock_s3.generate_presigned_url.return_value = "https://s3.example/download"
        mock_s3.head_object.return_value = {
            "ContentLength": 1024,
            "ContentType": "image/png",
        }
        mock_s3.delete_object.return_value = {}
        yield mock_s3


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def create_user_direct():
    def _create(username: str, password: str = "secret123", is_superuser: bool = False) -> int:
        from app.core.security import hash_password

        async def _run() -> int:
            async with TestSession() as session:
                user = User(
                    username=username,
                    hashed_password=await asyncio.to_thread(hash_password, password),
                    is_superuser=is_superuser,
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
                return user.id

        return run_db(_run())

    return _create