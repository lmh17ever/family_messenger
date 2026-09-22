from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.api.dependencies.session import get_session


async def get_user_by_username(username: str, db: AsyncSession) -> User | None:
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    return user
