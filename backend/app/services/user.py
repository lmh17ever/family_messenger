from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from sqlalchemy import select

from app.models.user import User
from app.api.dependencies.session import get_sesion


async def get_user_by_username(username: str, db: AsyncSession = Depends(get_sesion)) -> User:
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(404, "User not found")
    return user
