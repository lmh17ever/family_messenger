from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, or_
from sqlalchemy.orm import selectinload

from app.api.dependencies.session import get_session
from app.models.chat import Chat, ChatMember, ChatType
from app.schemas.chat import ChatCreate, ChatOut
from app.schemas.message import MessageOut
from app.schemas.attachment import AttachmentOut
from app.schemas.user import UserOut
from app.models.message import Message
from app.core.storage import presign_get
from app.core.config import settings


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
        .options(
            selectinload(Chat.members).selectinload(ChatMember.user),
            selectinload(Chat.last_message).selectinload(Message.sender),
            selectinload(Chat.last_message).selectinload(Message.attachments),
        )
        .join(ChatMember, ChatMember.chat_id == Chat.id)
        .where(ChatMember.user_id == user_id)
        .order_by(Chat.last_message_at.desc().nullslast(), Chat.id.desc())
        .offset(offset)
        .limit(limit)
    )

    result = await db.scalars(stmt)

    return list(result.all())

async def get_chat_for_user(db: AsyncSession, chat_id: int, user_id: int) -> Chat | None:
    stmt = (
        select(Chat)
        .join(ChatMember, ChatMember.chat_id == Chat.id)
        .where(Chat.id == chat_id, ChatMember.user_id == user_id)
        .options(
            selectinload(Chat.members).selectinload(ChatMember.user),
            selectinload(Chat.last_message).selectinload(Message.sender),
            selectinload(Chat.last_message).selectinload(Message.attachments),
        )
    )
    return await db.scalar(stmt)

async def mark_chat_read(
    db: AsyncSession, chat_id: int, user_id: int, message_id: int | None
) -> ChatMember | None:
    member = await db.scalar(
        select(ChatMember).where(
            ChatMember.chat_id == chat_id,
            ChatMember.user_id == user_id,
        )
    )
    if member is None:
        return None
    if message_id is None:
        message_id = await db.scalar(
            select(func.max(Message.id)).where(Message.chat_id == chat_id)
        )
    else:
        belongs_to_chat = await db.scalar(
            select(Message.id).where(
                Message.id == message_id,
                Message.chat_id == chat_id,
            )
        )
        if belongs_to_chat is None:
            return member
    if message_id is not None:
        member.last_read_message_id = message_id
        await db.commit()
        await db.refresh(member)
    return member

async def chat_to_out(db: AsyncSession, chat: Chat, user_id: int) -> ChatOut:
    member = next((item for item in chat.members if item.user_id == user_id), None)
    unread_count = 0
    if member and member.last_read_message_id is not None:
        unread_count = await db.scalar(
            select(func.count(Message.id)).where(
                Message.chat_id == chat.id,
                Message.id > member.last_read_message_id,
            )
        ) or 0
    elif member:
        unread_count = await db.scalar(
            select(func.count(Message.id)).where(Message.chat_id == chat.id)
        ) or 0

    last_message = None
    if chat.last_message:
        last_message = MessageOut(
            id=chat.last_message.id,
            chat_id=chat.last_message.chat_id,
            sender_id=chat.last_message.sender_id,
            text=chat.last_message.text,
            created_at=chat.last_message.created_at,
            sender=UserOut.from_user(chat.last_message.sender) if chat.last_message.sender else None,
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
                for attachment in chat.last_message.attachments
            ],
        )

    return ChatOut(
        id=chat.id,
        type=chat.type,
        title=chat.title,
        avatar_key=chat.avatar_key,
        created_at=chat.created_at,
        last_message_at=chat.last_message_at,
        participants=[UserOut.from_user(member.user) for member in chat.members],
        last_message=last_message,
        unread_count=unread_count,
    )

async def is_chat_member(db: AsyncSession, chat_id: int, user_id: int) -> bool:
    stmt = select(ChatMember.chat_id).where(ChatMember.chat_id == chat_id, ChatMember.user_id == user_id)
    return (await db.scalar(stmt)) is not None
