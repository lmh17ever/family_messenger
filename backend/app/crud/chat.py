from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.chat import CreateChat
from app.models.chat import Chat


async def create_chat(db: AsyncSession, chat_in: CreateChat) -> Chat:
    chat = Chat(
        user1_id=chat_in.user1_id,
        user2_id=chat_in.user2_id
    )
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return chat

async def get_chat(db: AsyncSession, chat_id) -> Chat | bool:
    chat = await db.get(Chat, chat_id)
    if chat is None:
        return False
    return chat

async def delete_chat(db: AsyncSession, chat_id: int) -> bool:
    chat = await db.get(Chat, chat_id)
    if chat is None:
        return False
    await db.delete(chat)
    await db.commit()
    return True