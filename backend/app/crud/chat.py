from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.chat import ChatCreate
from app.models.chat import Chat
from app.models.attachment import Attachment
from app.core.config import settings
from app.core.storage import delete_object


# async def create_chat(db: AsyncSession, chat_in: ChatCreate) -> Chat:
#     chat = Chat(
#         user1_id=chat_in.user1_id,
#         user2_id=chat_in.user2_id
#     )
#     db.add(chat)
#     await db.commit()
#     await db.refresh(chat)
#     return chat

# async def get_chat(db: AsyncSession, chat_id) -> Chat | bool:
#     chat = await db.get(Chat, chat_id)
#     if chat is None:
#         return False
#     return chat

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
    await db.delete(chat)
    await db.commit()
    for key in keys:
        await delete_object(settings.S3_PRIVATE_BUCKET, key)
    return True