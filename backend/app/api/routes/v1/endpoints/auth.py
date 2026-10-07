import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.session import get_session
from app.core.config import settings
from app.core.security import (
    authenticate_user,
    create_tokens,
    jwt,
)
from app.crud.user import create_user
from app.schemas.token import RefreshToken, Token, TokenData
from app.schemas.user import UserCreate
from app.services.user import get_user_by_id, get_user_by_username

router = APIRouter(prefix="/auth", tags=["auth"])


logger = logging.getLogger("__main__")


@router.post("/register", response_model=Token, summary="Register a new user")
async def register_user(user_in: UserCreate, db: AsyncSession = Depends(get_session)):
    existing_user_by_username = await get_user_by_username(db, user_in.username)
    if existing_user_by_username:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered")
    created_user = await create_user(db, user_in)
    return create_tokens(created_user.id)


@router.post("/token", response_model=Token, summary="Login to get access token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session),
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return create_tokens(user.id)


@router.post("/token/refresh", response_model=Token, summary="Refresh access token")
async def refresh_token(
    refresh_token: RefreshToken,
    db: AsyncSession = Depends(get_session),
):
    """Refresh access token using a valid refresh token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            refresh_token.refresh_token, settings.JWT_REFRESH_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except InvalidTokenError as e:
        logger.warning("refresh token decode failed: %s", e)
        raise credentials_exception from e

    subject = payload.get("sub")
    is_refresh = payload.get("refresh", False)
    if not isinstance(subject, str):
        logger.warning("refresh token has invalid 'sub'")
        raise credentials_exception
    if not is_refresh:
        logger.warning("Not is_refresh")
        raise credentials_exception
    try:
        token_data = TokenData.model_validate({"user_id": subject})
    except ValidationError as e:
        logger.warning("refresh token has invalid user id")
        raise credentials_exception from e
    user = await get_user_by_id(db, token_data.user_id)
    if user is None:
        logger.warning("user %s from refresh token not found", token_data.user_id)
        raise credentials_exception
    return create_tokens(user.id)
