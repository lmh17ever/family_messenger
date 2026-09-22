from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.storage import PresignRequest
from app.models.attachment import Attachment
from app.models.chat import Chat
from app.models.user import User
from app.core.config import settings
from app.core.storage import (
    MAX_ATTACHMENT_SIZE,
    DANGEROUS_INLINE_TYPES,
    presign_get,
    presign_post
)
from app.services.chat import is_chat_member
from app.core.storage import head_object


class AttachmentError(Exception):
    pass

class AttachmentNotFound(AttachmentError):
    pass

class AttachmentForbidden(AttachmentError):
    pass

class AttachmentInvalid(AttachmentError):
    pass


async def create_attachment_presign(
    db: AsyncSession, chat: Chat, user: User, data: PresignRequest
) -> tuple[Attachment, dict]:
    if data.content_type in DANGEROUS_INLINE_TYPES:
        raise AttachmentInvalid("content type not allowed")
    if not (0 < data.size <= MAX_ATTACHMENT_SIZE):
        raise AttachmentInvalid("size not allowed")

    key = f"chats/{chat.id}/{uuid4().hex}"
    attachment = Attachment(
        key=key, chat_id=chat.id, uploader_id=user.id,
        filename=data.filename, content_type=data.content_type, size=data.size,
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)

    upload = presign_post(settings.S3_PRIVATE_BUCKET, key, data.content_type, data.size)
    return attachment, upload


async def resolve_attachments_for_message(
    db: AsyncSession, chat_id: int, user_id: int, attachment_ids: list[int]
) -> list[Attachment]:
    if not attachment_ids:
        return []
    stmt = select(Attachment).where(Attachment.id.in_(attachment_ids))
    attachments = list((await db.scalars(stmt)).all())

    found_ids = {a.id for a in attachments}
    missing = set(attachment_ids) - found_ids
    if missing:
        raise AttachmentNotFound(f"unknown attachment ids: {missing}")

    for att in attachments:
        if att.chat_id != chat_id or att.uploader_id != user_id:
            raise AttachmentForbidden(f"attachment {att.id} not accessible")
        if att.message_id is not None:
            raise AttachmentInvalid(f"attachment {att.id} already attached")

    return attachments

async def get_attachment_download_url(db: AsyncSession, attachment_id: int, user_id: int) -> str:
    attachment = await db.get(Attachment, attachment_id)
    if attachment is None:
        raise AttachmentNotFound()
    if not await is_chat_member(db, attachment.chat_id, user_id):
        raise AttachmentForbidden()
    return presign_get(
        settings.S3_PRIVATE_BUCKET,
        attachment.key,
        attachment.filename,
        attachment.content_type,
    )

async def confirm_attachment(
    db: AsyncSession,
    attachment: Attachment,
) -> Attachment:
    head = await head_object(
        settings.S3_PRIVATE_BUCKET,
        attachment.key,
    )

    if head is None:
        raise AttachmentInvalid("object not found")

    actual_size = head["ContentLength"]
    actual_content_type = head["ContentType"]

    if actual_size <= 0 or actual_size > MAX_ATTACHMENT_SIZE:
        raise AttachmentInvalid("invalid object size")

    if actual_content_type in DANGEROUS_INLINE_TYPES:
        raise AttachmentInvalid("content type not allowed")

    attachment.size = actual_size
    attachment.content_type = actual_content_type

    await db.commit()
    await db.refresh(attachment)

    return attachment
