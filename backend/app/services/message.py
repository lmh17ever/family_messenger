from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.message import Message


async def get_user_messages(db: AsyncSession, chat_id: int, offset: int = 0, limit: int = 100) -> list[Message]:
    stmt = select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at.desc()).offset(offset).limit(limit)
    reslut = await db.execute(stmt)
    return list(reslut.scalars().all())
