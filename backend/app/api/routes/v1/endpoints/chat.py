from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.chat import get_chat_as_member
from app.api.dependencies.session import get_session
from app.core.security import get_current_user
from app.crud.chat import delete_chat
from app.models.chat import Chat, ChatMember, ChatType
from app.models.message import Message
from app.models.user import User
from app.schemas.attachment import AvatarPresignOut
from app.schemas.chat import (
    ChatAvatarConfirmIn,
    ChatAvatarPresignIn,
    ChatMemberIn,
    ChatOut,
    ChatReadIn,
    GroupChatCreate,
)
from app.services.chat import (
    add_chat_member,
    chat_to_out,
    chat_to_out_for_user,
    confirm_chat_avatar,
    create_chat_avatar_presign,
    create_group_chat,
    get_chat_for_user,
    get_my_chats,
    get_or_create_chat_by_user_ids,
    get_unread_counts,
    mark_chat_read,
    remove_chat_member,
)
from app.services.attachments import AttachmentInvalid

router = APIRouter(prefix="/chats", tags=["chats"])


@router.post("/{user_id}", response_model=ChatOut, name="Open Chat")
async def get_or_create_chat_enpoint(
    user_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    chat = await get_or_create_chat_by_user_ids(
        db=db,
        user1_id=current_user.id,
        user2_id=user_id
    )
    chat = await get_chat_for_user(db, chat.id, current_user.id)
    return await chat_to_out_for_user(db, chat, current_user.id)

@router.post("", response_model=ChatOut, name="Create group chat")
async def create_group_chat_endpoint(
    data: GroupChatCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    chat = await create_group_chat(db, current_user.id, data.title, data.member_ids)
    chat = await get_chat_for_user(db, chat.id, current_user.id)
    return await chat_to_out_for_user(db, chat, current_user.id)

@router.get("/my", response_model=list[ChatOut], name="Get my chats")
async def get_my_chats_endpoint(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    offset: int = 0,
    limit: int = 100
):
      chats = await get_my_chats(
           user_id=current_user.id,
           db=db,
           offset=offset,
           limit=limit
      )
      unread_counts = await get_unread_counts(db, [chat.id for chat in chats], current_user.id)
      return [chat_to_out(chat, unread_counts.get(chat.id, 0)) for chat in chats]

@router.get("/{chat_id}", response_model=ChatOut, name="Get chat")
async def get_chat_endpoint(
    chat_id: int,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    chat = await get_chat_for_user(db, chat_id, user.id)
    if chat is None:
        raise HTTPException(404, "Chat not found")
    return await chat_to_out_for_user(db, chat, user.id)

@router.post("/{chat_id}/read", response_model=ChatOut, name="Mark chat as read")
async def mark_chat_read_endpoint(
    chat_id: int,
    data: ChatReadIn,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    chat = await get_chat_for_user(db, chat_id, user.id)

    if chat is None:
        raise HTTPException(404, "Chat not found")

    member = await db.scalar(
        select(ChatMember).where(
            ChatMember.chat_id == chat.id,
            ChatMember.user_id == user.id,
        )
    )
    assert member is not None

    if data.message_id is None:
        last_message = await db.scalar(
            select(func.max(Message.id)).where(Message.chat_id == chat.id)
        )
        if last_message is None:
            raise HTTPException(400, "No messages yet in the chat")
        data.message_id = last_message

    belongs_to_chat = await db.scalar(
        select(Message.id).where(
            Message.id == data.message_id,
            Message.chat_id == chat.id,
        )
    )
    if not belongs_to_chat:
        raise HTTPException(400, "This message doesn't belong to the chat")

    await mark_chat_read(db, member, data.message_id)
    return await chat_to_out_for_user(db, chat, user.id)

@router.post("/{chat_id}/avatar/presign", response_model=AvatarPresignOut, name="Presign group avatar")
async def presign_group_avatar(
    data: ChatAvatarPresignIn,
    chat: Chat = Depends(get_chat_as_member),
):
    try:
        return await create_chat_avatar_presign(chat, data.content_type, data.size)
    except AttachmentInvalid as e:
        raise HTTPException(422, str(e))

@router.post("/{chat_id}/avatar/confirm", response_model=ChatOut, name="Confirm group avatar")
async def confirm_group_avatar(
    data: ChatAvatarConfirmIn,
    chat: Chat = Depends(get_chat_as_member),
    db: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    try:
        await confirm_chat_avatar(db, chat, data.avatar_key)
    except AttachmentInvalid as e:
        raise HTTPException(422, str(e))
    updated_chat = await get_chat_for_user(db, chat.id, user.id)
    if updated_chat is None:
        raise HTTPException(404, detail="Chat not found")
    return await chat_to_out_for_user(db, chat=updated_chat, user_id=user.id)

@router.post("/{chat_id}/members", status_code=201, name="Add chat member")
async def add_member(
    data: ChatMemberIn,
    chat: Chat = Depends(get_chat_as_member),
    db: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    if chat.type != ChatType.GROUP or chat.creator_id != user.id:
        raise HTTPException(403, "Only the chat creator can manage members")
    return await add_chat_member(db, chat.id, data.user_id)

@router.delete("/{chat_id}/members/{user_id}", status_code=204, name="Remove chat member")
async def remove_member(
    user_id: int,
    chat: Chat = Depends(get_chat_as_member),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if chat.type != ChatType.GROUP or chat.creator_id != current_user.id:
        raise HTTPException(403, "Only the chat creator can manage members")
    await remove_chat_member(db, chat.id, user_id)

@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT, name="Delete chat")
async def delete_chat_endpoint(
    chat: Chat = Depends(get_chat_as_member),
    db: AsyncSession = Depends(get_session),
):
    deleted = await delete_chat(db, chat.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat not found")
