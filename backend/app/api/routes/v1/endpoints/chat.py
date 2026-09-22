from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException

from app.schemas.chat import ChatOut
from app.api.dependencies.session import get_session
from app.models.user import User
from app.models.chat import Chat
from app.core.security import get_current_user
from app.api.dependencies.chat import get_chat_as_member
from app.services.chat import get_or_create_chat_by_user_ids, get_my_chats
from app.crud.chat import delete_chat


router = APIRouter(prefix="/chats", tags=["chats"])


@router.post("/{user_id}", response_model=ChatOut, name="Open Chat")
async def get_or_create_chat_enpoint(
    user_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return  await get_or_create_chat_by_user_ids(
        db=db,
        user1_id=current_user.id,
        user2_id=user_id
    )

@router.get("/my", response_model=list[ChatOut], name="Get my chats")
async def get_my_chats_endpoint(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    offset: int = 0,
    limit: int = 100
):
      return await get_my_chats(
           user_id=current_user.id,
           db=db,
           offset=offset,
           limit=limit
      )

@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT, name="Delete chat")
async def delete_chat_endpoint(
    chat: Chat = Depends(get_chat_as_member),
    db: AsyncSession = Depends(get_session),
):
    deleted = await delete_chat(db, chat.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat not found")
