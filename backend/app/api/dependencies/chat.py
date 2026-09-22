# dependencies.py

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.session import get_session
from app.core.security import get_current_user
from app.models.chat import Chat, ChatMember
from app.models.user import User


async def get_chat_as_member(
    chat_id: int,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> Chat:
    stmt = (
        select(Chat)
        .join(ChatMember, ChatMember.chat_id == Chat.id)
        .where(Chat.id == chat_id, ChatMember.user_id == user.id)
    )
    chat = await db.scalar(stmt)
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat
