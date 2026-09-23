from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import selectinload

from app.models.message import Message
from app.models.chat import Chat
from app.models.attachment import Attachment
from app.schemas.message import MessageCreate
from app.services.attachments import resolve_attachments_for_message
from app.core.config import settings
from app.core.storage import delete_object


async def create_message(db: AsyncSession, chat: Chat, sender_id: int, message_in: MessageCreate) -> Message:
    if chat is None:
        raise HTTPException(404, "Chat not found")
    attachments = await resolve_attachments_for_message(db, chat.id, sender_id, message_in.attachment_ids)
    message = Message(
        text=message_in.text,
        chat_id=chat.id,
        sender_id=sender_id,
    )
    db.add(message)
    await db.flush()
    chat.last_message_at = func.now()
    chat.last_message_id = message.id
    for att in attachments:
        att.message_id = message.id
    await db.commit()
    result = await db.execute(
        select(Message)
        .options(selectinload(Message.sender), selectinload(Message.attachments))
        .where(Message.id == message.id)
    )
    return result.scalar_one()

async def delete_message(db: AsyncSession, message_id) -> bool:
    message = await db.get(Message, message_id)
    if message is None:
        return False
    keys = list(
        (
            await db.scalars(
                select(Attachment.key).where(Attachment.message_id == message_id)
            )
        ).all()
    )
    chat = await db.get(Chat, message.chat_id)
    was_last_message = chat is not None and chat.last_message_id == message.id
    await db.delete(message)
    if was_last_message and chat is not None:
        replacement = await db.scalar(
            select(Message.id)
            .where(Message.chat_id == message.chat_id, Message.id != message.id)
            .order_by(Message.id.desc())
            .limit(1)
        )
        chat.last_message_id = replacement
        chat.last_message_at = (
            await db.scalar(
                select(func.max(Message.created_at)).where(
                    Message.chat_id == message.chat_id,
                    Message.id != message.id,
                )
            )
        )
    await db.commit()
    for key in keys:
        await delete_object(settings.S3_PRIVATE_BUCKET, key)
    return True
