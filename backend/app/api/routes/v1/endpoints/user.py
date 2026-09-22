from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserOut, UserCreate
from app.api.dependencies.session import get_session
from app.crud.user import create_user, delete_user, get_user, get_users
from app.models.user import User
from app.core.security import get_current_user
from app.schemas.attachment import AvatarPresignOut
from app.schemas.storage import AvatarConfirmIn, PresignRequest
from app.services.attachments import AttachmentInvalid
from app.services.avatars import confirm_avatar, create_avatar_presign


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/signup", response_model=UserOut, name="Create user")
async def create_user_endpoint(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_session)
):
    user = await create_user(db, user_in)
    return user

@router.get("/me", response_model=UserOut, name="Get my user")
async def get_my_user_endpoint(
    user: User = Depends(get_current_user)
):
    return UserOut.from_user(user)

@router.post("/me/avatar/presign", response_model=AvatarPresignOut)
async def presign_avatar(
    avatar_in: PresignRequest,
    user: User = Depends(get_current_user),
):
    try:
        return await create_avatar_presign(user, avatar_in.content_type, avatar_in.size)
    except AttachmentInvalid as e:
        raise HTTPException(422, str(e))


@router.post("/me/avatar/confirm", response_model=UserOut)
async def confirm_avatar_endpoint(
    avatar_in: AvatarConfirmIn,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    try:
        user = await confirm_avatar(db, user, avatar_in.avatar_key)
    except AttachmentInvalid as e:
        raise HTTPException(422, str(e))
    return UserOut.from_user(user)

@router.get("/", response_model=list[UserOut], name="Get user list")
async def get_users_endpoint(
    db: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
    offset: int = 0,
    limit: int = 100
):
    users = await get_users(db, offset=offset, limit=limit)
    return [UserOut.from_user(user) for user in users]

@router.get("/{user_id}", response_model=UserOut, name="Get user")
async def get_user_endpoint(
    user_id: int,
    db: AsyncSession = Depends(get_session)
):
    user = await get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut.from_user(user)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, name="Delete user")
async def delete_user_endpoint(
    user_id: int,
    db: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    deleted = await delete_user(db, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
