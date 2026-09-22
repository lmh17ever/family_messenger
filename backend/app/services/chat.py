from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from fastapi import Depends

from app.api.dependencies.session import get_session
from app.models.chat import Chat, ChatMember, ChatType
from app.schemas.chat import ChatCreate


async def get_or_create_chat_by_user_ids(
    user1_id: int,
    user2_id: int,
    db: AsyncSession,
) -> Chat:
    user1_id, user2_id = sorted((user1_id, user2_id))
    direct_key = f"{user1_id}_{user2_id}"

    stmt = select(Chat).where(Chat.direct_key == direct_key)
    chat = await db.scalar(stmt)

    if chat is not None:
        return chat

    chat = Chat(
        type=ChatType.DIRECT,
        direct_key=direct_key,
    )
    db.add(chat)
    await db.flush()

    db.add_all(
        [
            ChatMember(chat_id=chat.id, user_id=user1_id),
            ChatMember(chat_id=chat.id, user_id=user2_id),
        ]
    )

    await db.commit()
    await db.refresh(chat)

    return chat

async def create_group_chat(
    db: AsyncSession,
    creator_id: int,
    title: str,
    member_ids: list[int],
) -> Chat:
    chat = Chat(
        type=ChatType.GROUP,
        title=title,
    )
    db.add(chat)
    await db.flush()

    user_ids = set(member_ids)
    user_ids.add(creator_id)

    db.add_all(
        [
            ChatMember(chat_id=chat.id, user_id=user_id)
            for user_id in user_ids
        ]
    )

    await db.commit()
    await db.refresh(chat)

    return chat

async def get_my_chats(db: AsyncSession, user_id: int, offset: int = 0, limit: int = 100) -> list[Chat]:
    stmt = (
        select(Chat)
        .join(ChatMember, ChatMember.chat_id == Chat.id)
        .where(ChatMember.user_id == user_id)
        .order_by(Chat.last_message_at.desc().nullslast())
        .offset(offset)
        .limit(limit)
    )

    result = await db.scalars(stmt)

    return list(result.all())

async def is_chat_member(db: AsyncSession, chat_id: int, user_id: int) -> bool:
    stmt = select(ChatMember.chat_id).where(ChatMember.chat_id == chat_id, ChatMember.user_id == user_id)
    return (await db.scalar(stmt)) is not None
