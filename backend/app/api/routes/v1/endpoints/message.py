from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException

from app.schemas.message import MessageOut, MessageCreate
from app.api.dependencies.session import get_session
from app.api.dependencies.chat import get_chat_as_member
from app.crud.message import create_message
from app.services.message import get_user_messages
from app.core.security import get_current_user
from app.models.user import User
from app.models.chat import Chat
from app.services.attachments import AttachmentForbidden, AttachmentInvalid, AttachmentNotFound


router = APIRouter(prefix="/chats/{chat_id}/messages", tags=["messages"])


@router.post("/", response_model=MessageOut, name="Create message")
async def create_message_endpoint(
    message_in: MessageCreate,
    chat: Chat = Depends(get_chat_as_member),
    db: AsyncSession = Depends(get_session),
    sender: User = Depends(get_current_user),
):
    try:
        return await create_message(db, chat, sender.id, message_in)
    except AttachmentNotFound:
        raise HTTPException(422, "unknown attachment")
    except AttachmentForbidden:
        raise HTTPException(403, "attachment not accessible")
    except AttachmentInvalid as e:
        raise HTTPException(422, str(e))

@router.get("/", response_model=list[MessageOut], name="Get messages")
async def get_messages_endpoint(
    chat: Chat = Depends(get_chat_as_member),
    offset:int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_session)
):
    return await get_user_messages(
        db=db,
        chat_id=chat.id,
        offset=offset,
        limit=limit
    )
