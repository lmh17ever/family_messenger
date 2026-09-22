from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.services.attachments import AttachmentInvalid
from app.core.storage import ALLOWED_IMAGE_TYPES, MAX_AVATAR_SIZE, delete_object, head_object, presign_post
from app.models.user import User
from app.schemas.attachment import AvatarPresignOut
from app.core.config import settings


async def create_avatar_presign(user: User, content_type: str, size: int) -> AvatarPresignOut:
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise AttachmentInvalid("content type not allowed")
    if not (0 < size <= MAX_AVATAR_SIZE):
        raise AttachmentInvalid("size not allowed")

    ext = content_type.split("/")[1]
    key = f"{user.id}/{uuid4().hex}.{ext}"
    upload = presign_post(settings.S3_PUBLIC_BUCKET, key, content_type, size)
    return AvatarPresignOut(upload=upload, avatar_key=key)


async def confirm_avatar(db: AsyncSession, user: User, avatar_key: str) -> User:
    expected_prefix = f"{user.id}/"
    if not avatar_key.startswith(expected_prefix):
        raise AttachmentInvalid("invalid avatar key")
    obj = await head_object(settings.S3_PUBLIC_BUCKET, avatar_key)
    if obj is None:
        raise AttachmentInvalid("file not found in storage")

    old_key = user.avatar_key
    user.avatar_key = avatar_key
    await db.commit()
    await db.refresh(user)

    if old_key and old_key != avatar_key:
        await delete_object(settings.S3_PUBLIC_BUCKET, old_key)

    return user
