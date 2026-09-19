from datetime import datetime, UTC

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.models.chat import Chat
from app.schemas.message import CreateMessage


async def create_message(db: AsyncSession, message_in: CreateMessage) -> Message:
    message = Message(
        text=message_in.text,
        chat_id=message_in.chat_id,
        sender_id=message_in.sender_id
    )
    db.add(message)
    chat = await db.get(Chat, message_in.chat_id)
    if chat is not None:
        chat.last_message_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(message)
    return message

async def delete_message(db: AsyncSession, message_id) -> bool:
    message = await db.get(Message, message_id)
    if message is None:
        return False
    await db.delete(message)
    await db.commit()
    return True
