from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from fastapi import Depends

from app.api.dependencies.session import get_sesion
from app.models.chat import Chat
from app.crud.chat import create_chat
from app.schemas.chat import CreateChat


async def get_or_create_chat_by_user_ids(
        user1_id: int,
        user2_id: int,
        db: AsyncSession = Depends(get_sesion),
        ) -> Chat:
    user1_id, user2_id = sorted((user1_id, user2_id))
    stmt = select(Chat).where(Chat.user1_id == user1_id, Chat.user2_id == user2_id)
    result = await db.execute(stmt)
    chat = result.scalar_one_or_none()

    if chat is None:
        chat = await create_chat(
            db=db,
            chat_in=CreateChat(
                user1_id=user1_id,
                user2_id=user2_id
            )
        )
    return chat

async def get_my_chats(db: AsyncSession, user_id: int, offset: int = 0, limit: int = 100) -> list[Chat]:
    stmt = select(Chat).where(or_(Chat.user1_id == user_id, Chat.user2_id == user_id)).order_by(Chat.last_message_at.desc().nullslast()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())
