from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException

from app.schemas.chat import (
    ChatAvatarConfirmIn,
    ChatAvatarPresignIn,
    ChatMemberIn,
    ChatOut,
    ChatReadIn,
    GroupChatCreate,
)
from app.schemas.attachment import AvatarPresignOut
from app.api.dependencies.session import get_session
from app.models.user import User
from app.models.chat import Chat, ChatType
from app.core.security import get_current_user
from app.api.dependencies.chat import get_chat_as_member
from app.services.chat import (
    chat_to_out,
    add_chat_member,
    confirm_chat_avatar,
    create_chat_avatar_presign,
    create_group_chat,
    get_chat_for_user,
    get_my_chats,
    get_or_create_chat_by_user_ids,
    mark_chat_read,
    remove_chat_member,
)
from app.crud.chat import delete_chat


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
    return await chat_to_out(db, chat, current_user.id)

@router.post("", response_model=ChatOut, name="Create group chat")
async def create_group_chat_endpoint(
    data: GroupChatCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    chat = await create_group_chat(db, current_user.id, data.title, data.member_ids)
    chat = await get_chat_for_user(db, chat.id, current_user.id)
    return await chat_to_out(db, chat, current_user.id)

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
      return [await chat_to_out(db, chat, current_user.id) for chat in chats]

@router.get("/{chat_id}", response_model=ChatOut, name="Get chat")
async def get_chat_endpoint(
    chat_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    chat = await get_chat_for_user(db, chat_id, current_user.id)
    if chat is None:
        raise HTTPException(404, "Chat not found")
    return await chat_to_out(db, chat, current_user.id)

@router.post("/{chat_id}/read", response_model=ChatOut, name="Mark chat as read")
async def mark_chat_read_endpoint(
    chat_id: int,
    data: ChatReadIn,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    member = await mark_chat_read(db, chat_id, current_user.id, data.message_id)
    if member is None:
        raise HTTPException(404, "Chat not found")
    chat = await get_chat_for_user(db, chat_id, current_user.id)
    return await chat_to_out(db, chat, current_user.id)

@router.post("/{chat_id}/avatar/presign", response_model=AvatarPresignOut, name="Presign group avatar")
async def presign_group_avatar(
    chat_id: int,
    data: ChatAvatarPresignIn,
    chat: Chat = Depends(get_chat_as_member),
):
    return await create_chat_avatar_presign(chat, data.content_type, data.size)

@router.post("/{chat_id}/avatar/confirm", response_model=ChatOut, name="Confirm group avatar")
async def confirm_group_avatar(
    chat_id: int,
    data: ChatAvatarConfirmIn,
    chat: Chat = Depends(get_chat_as_member),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    chat = await confirm_chat_avatar(db, chat, data.avatar_key)
    return await chat_to_out(db, chat, current_user.id)

@router.post("/{chat_id}/members", status_code=201, name="Add chat member")
async def add_member(
    chat_id: int,
    data: ChatMemberIn,
    chat: Chat = Depends(get_chat_as_member),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if chat.type != ChatType.GROUP or chat.creator_id != current_user.id:
        raise HTTPException(403, "Only the chat creator can manage members")
    return await add_chat_member(db, chat.id, data.user_id)

@router.delete("/{chat_id}/members/{user_id}", status_code=204, name="Remove chat member")
async def remove_member(
    chat_id: int,
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
