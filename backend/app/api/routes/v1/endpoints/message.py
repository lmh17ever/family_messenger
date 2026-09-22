from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException

from app.schemas.message import MessageOut, MessageCreate, MessageUpdate
from app.api.dependencies.session import get_session
from app.api.dependencies.chat import get_chat_as_member
from app.crud.message import create_message, delete_message
from app.services.message import get_user_messages, message_to_out, update_message
from app.core.security import get_current_user
from app.models.user import User
from app.models.chat import Chat
from app.models.message import Message
from app.services.attachments import AttachmentForbidden, AttachmentInvalid, AttachmentNotFound
from app.services.realtime import chat_connections


router = APIRouter(prefix="/chats/{chat_id}/messages", tags=["messages"])


@router.post("", response_model=MessageOut, name="Create message")
async def create_message_endpoint(
    message_in: MessageCreate,
    chat: Chat = Depends(get_chat_as_member),
    db: AsyncSession = Depends(get_session),
    sender: User = Depends(get_current_user),
):
    try:
        message = await create_message(db, chat, sender.id, message_in)
        response = await message_to_out(message)
        await chat_connections.broadcast(
            chat.id,
            {"type": "message.created", "message": response.model_dump(mode="json")},
        )
        await chat_connections.broadcast_chat_users(
            db, chat.id, {"type": "chat.updated", "chat_id": chat.id}
        )
        await chat_connections.notify_new_message(
            db, chat.id, response.model_dump(mode="json"), sender.id
        )
        return response
    except AttachmentNotFound:
        raise HTTPException(422, "unknown attachment")
    except AttachmentForbidden:
        raise HTTPException(403, "attachment not accessible")
    except AttachmentInvalid as e:
        raise HTTPException(422, str(e))

@router.get("", response_model=list[MessageOut], name="Get messages")
async def get_messages_endpoint(
    chat: Chat = Depends(get_chat_as_member),
    offset:int = 0,
    limit: int = 100,
    search: str | None = None,
    db: AsyncSession = Depends(get_session)
):
    messages = await get_user_messages(
        db=db,
        chat_id=chat.id,
        offset=offset,
        limit=limit,
        search=search,
    )
    return [await message_to_out(message) for message in messages]

@router.patch("/{message_id}", response_model=MessageOut, name="Edit message")
async def update_message_endpoint(
    message_id: int,
    message_in: MessageUpdate,
    chat: Chat = Depends(get_chat_as_member),
    sender: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    message = await db.get(Message, message_id)
    if message is None or message.chat_id != chat.id or message.sender_id != sender.id:
        raise HTTPException(404, "Message not found")
    updated = await update_message(db, message_id, message_in.text)
    response = await message_to_out(updated)
    await chat_connections.broadcast(
        chat.id,
        {"type": "message.updated", "message": response.model_dump(mode="json")},
    )
    return response

@router.delete("/{message_id}", status_code=204, name="Delete message")
async def delete_message_endpoint(
    message_id: int,
    chat: Chat = Depends(get_chat_as_member),
    sender: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    message = await db.get(Message, message_id)
    if message is None or message.chat_id != chat.id or message.sender_id != sender.id:
        raise HTTPException(404, "Message not found")
    await delete_message(db, message_id)
    await chat_connections.broadcast(
        chat.id,
        {"type": "message.deleted", "message_id": message_id, "chat_id": chat.id},
    )
