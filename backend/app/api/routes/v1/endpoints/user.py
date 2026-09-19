from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserOut, CreateUser
from app.api.dependencies.session import get_sesion
from app.crud.user import create_user, delete_user, get_user, get_users


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/signup", response_model=UserOut, name="Create user")
async def create_user_endpoint(
    user_in: CreateUser,
    db: AsyncSession = Depends(get_sesion)
):
    user = await create_user(db, user_in)
    return user

@router.get("/{user_id}", response_model=UserOut, name="Get user")
async def get_user_endpoint(
    user_id: int,
    db: AsyncSession = Depends(get_sesion)
):
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/", response_model=list[UserOut], name="Get user list")
async def get_users_endpoint(
    db: AsyncSession = Depends(get_sesion),
    offset: int = 0,
    limit: int = 100
):
    return await get_users(db, offset=offset, limit=limit)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, name="Delete user")
async def delete_user_endpoint(
    user_id: int,
    db: AsyncSession = Depends(get_sesion)
):
    deleted = await delete_user(db, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
