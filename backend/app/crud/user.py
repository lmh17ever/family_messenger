from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.user import CreateUser
from app.models.user import User
from app.core.security import hash_password


async def create_user(db: AsyncSession, user_in: CreateUser) -> User:
    user = User(
        username=user_in.username,
        hashed_password=hash_password(user_in.password)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def get_user(db: AsyncSession, user_id) -> User | bool:
    user = await db.get(User, user_id)
    if user is None:
        return False
    return user

async def get_users(db: AsyncSession, offset: int = 0, limit: int = 100) -> list[User]:
    stmt = select(User).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def delete_user(db: AsyncSession, user_id: int) -> bool:
    user = await db.get(User, user_id)
    if user is None:
        return False

    await db.delete(user)
    await db.commit()
    return True
