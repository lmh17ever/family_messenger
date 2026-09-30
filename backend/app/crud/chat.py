from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.chat import Chat
from app.models.attachment import Attachment
from app.core.config import settings
from app.core.storage import delete_object


async def delete_chat(db: AsyncSession, chat_id: int) -> bool:
    chat = await db.get(Chat, chat_id)
    if chat is None:
        return False
    keys = list(
        (
            await db.scalars(
                select(Attachment.key).where(Attachment.chat_id == chat_id)
            )
        ).all()
    )
    for key in keys:
        await delete_object(settings.S3_PRIVATE_BUCKET, key)
    await db.delete(chat)
    await db.commit()
    return True
