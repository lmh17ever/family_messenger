from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.message import Message
from app.schemas.attachment import AttachmentOut
from app.schemas.message import MessageOut
from app.schemas.user import UserOut
from app.core.config import settings
from app.core.storage import presign_get


async def get_user_messages(
    db: AsyncSession,
    chat_id: int,
    offset: int = 0,
    limit: int = 100,
    search: str | None = None,
) -> list[Message]:
    stmt = (
        select(Message)
        .options(selectinload(Message.sender), selectinload(Message.attachments))
        .where(Message.chat_id == chat_id)
        .order_by(Message.id.desc())
        .offset(offset)
        .limit(limit)
    )
    if search:
        stmt = stmt.where(Message.text.ilike(f"%{search}%"))
    reslut = await db.execute(stmt)
    return list(reslut.scalars().all())

async def message_to_out(message: Message) -> MessageOut:
    return MessageOut(
        id=message.id,
        chat_id=message.chat_id,
        sender_id=message.sender_id,
        text=message.text,
        created_at=message.created_at,
        sender=UserOut.from_user(message.sender) if message.sender else None,
        attachments=[
            AttachmentOut(
                id=attachment.id,
                filename=attachment.filename,
                content_type=attachment.content_type,
                size=attachment.size,
                url=presign_get(
                    settings.S3_PRIVATE_BUCKET,
                    attachment.key,
                    attachment.filename,
                    attachment.content_type,
                ),
            )
            for attachment in message.attachments
        ],
    )

async def update_message(db: AsyncSession, message_id: int, text: str | None) -> Message | None:
    message = await db.get(Message, message_id)
    if message is None:
        return None
    message.text = text
    await db.commit()
    await db.refresh(message)
    await db.refresh(message, ["sender", "attachments"])
    return message
