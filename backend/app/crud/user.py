from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.user import UserCreate
from app.models.user import User
from app.models.attachment import Attachment
from app.core.security import hash_password
from app.core.config import settings
from app.core.storage import delete_object


async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    user = User(
        username=user_in.username,
        hashed_password=hash_password(user_in.password)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def get_user(db: AsyncSession, user_id) -> User | None:
    return await db.get(User, user_id)

async def get_users(db: AsyncSession, offset: int = 0, limit: int = 100) -> list[User]:
    stmt = select(User).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def delete_user(db: AsyncSession, user_id: int) -> bool:
    user = await db.get(User, user_id)
    if user is None:
        return False

    keys = list(
        (
            await db.scalars(
                select(Attachment.key).where(Attachment.uploader_id == user_id)
            )
        ).all()
    )
    avatar_key = user.avatar_key
    await db.delete(user)
    await db.commit()
    for key in keys:
        await delete_object(settings.S3_PRIVATE_BUCKET, key)
    if avatar_key:
        await delete_object(settings.S3_PUBLIC_BUCKET, avatar_key)
    return True
