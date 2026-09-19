from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends

from app.schemas.message import MessageOut, CreateMessage
from app.api.dependencies.session import get_sesion
from app.crud.message import create_message
from app.services.message import get_user_messages
from app.core.security import get_current_user
from app.models.user import User


router = APIRouter(prefix="/chats/{chat_id}/messages", tags=["messages"])


@router.post("/", response_model=MessageOut, name="Create message")
async def create_message_enpoint(
    chat_id: int,
    text: str,
    db: AsyncSession = Depends(get_sesion),
    sender: User = Depends(get_current_user)
):
    message_data = CreateMessage(
        chat_id=chat_id,
        text=text,
        sender_id=sender.id
    )
    message = await create_message(db, message_data)
    return message


@router.get("/", response_model=list[MessageOut], name="Get messages")
async def get_messages_endpoint(
    chat_id: int,
    offset:int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_sesion)
):
    return await get_user_messages(
        db=db,
        chat_id=chat_id,
        offset=offset,
        limit=limit
    )
