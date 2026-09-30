from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from app.models.message import Message
from app.schemas.attachment import AttachmentOut
from app.schemas.message import MessageOut
from app.schemas.user import UserOut
from app.core.config import settings
from app.core.storage import presign_get


async def get_user_messages(
    db: AsyncSession,
    chat_id: int,
    before_id: int | None = None,
    limit: int = 100,
    search: str | None = None,
) -> list[Message]:
    stmt = select(Message).where(Message.chat_id == chat_id)
    if before_id:
        stmt = stmt.where(Message.id < before_id)
    stmt = (
        stmt
        .options(joinedload(Message.sender), selectinload(Message.attachments))
        .order_by(Message.id.desc())
        .limit(limit)
    )
    if search:
        stmt = stmt.where(Message.text.icontains(search, autoescape=True))
    result = await db.execute(stmt)
    return list(result.scalars().all())

def message_to_out(message: Message) -> MessageOut:
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

async def update_message(db: AsyncSession, message: Message, text: str | None) -> Message:
    message.text = text
    await db.commit()
    await db.refresh(message, ["sender", "attachments"])
    return message
