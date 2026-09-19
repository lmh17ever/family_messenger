from app.db.base import AsyncSessionLocal


async def get_sesion():
    async with AsyncSessionLocal() as session:
        yield session
