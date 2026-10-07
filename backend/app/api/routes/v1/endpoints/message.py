from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status

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
from app.core.realtime.redis_manager import redis_manager
from app.services.realtime.event_service import event_service
from app.core.config import settings


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
        response = message_to_out(message)
        response_json = response.model_dump(mode="json")
        await redis_manager.publish(
            event_service.generate_chat_channel_name(chat.id),
            {"type": "message.created", "message": response_json},
        )
        await event_service.broadcast_chat_users(
            db, chat.id, {"type": "chat.updated", "chat_id": chat.id}
        )
        await event_service.notify_new_message(
            db, chat.id, response_json, sender.id
        )
        return response
    except AttachmentNotFound:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "unknown attachment")
    except AttachmentForbidden:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "attachment not accessible")
    except AttachmentInvalid as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e))

@router.get("", response_model=list[MessageOut], name="Get messages")
async def get_messages_endpoint(
    chat: Chat = Depends(get_chat_as_member),
    before_id:int | None = None,
    limit: int = settings.DEFAULT_LIMIT,
    search: str | None = None,
    db: AsyncSession = Depends(get_session)
):
    messages = await get_user_messages(
        db=db,
        chat_id=chat.id,
        before_id=before_id,
        limit=limit,
        search=search,
    )
    return [message_to_out(message) for message in messages]

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
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Message not found")
    updated = await update_message(db, message, message_in.text)
    response = message_to_out(updated)
    await redis_manager.publish(
        event_service.generate_chat_channel_name(chat.id),
        {"type": "message.updated", "message": response.model_dump(mode="json")},
    )
    return response

@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT, name="Delete message")
async def delete_message_endpoint(
    message_id: int,
    chat: Chat = Depends(get_chat_as_member),
    sender: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    message = await db.get(Message, message_id)
    if message is None or message.chat_id != chat.id or message.sender_id != sender.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Message not found")
    await delete_message(db, message_id)
    await redis_manager.publish(
        event_service.generate_chat_channel_name(chat.id),
        {"type": "message.deleted", "message_id": message_id, "chat_id": chat.id},
    )
