from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from jwt.exceptions import InvalidTokenError

from app.core.security import (
    authenticate_user,
    create_tokens,
    jwt,
)
from app.schemas.token import RefreshToken, Token
from app.schemas.user import CreateUser
from app.core.config import settings
from app.services.user import get_user_by_username
from app.crud.user import create_user
from app.api.dependencies.session import get_sesion

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register/", response_model=Token, summary="Register a new user")
async def register_user(user_in: CreateUser, db: AsyncSession = Depends(get_sesion)):
    """Register a new user account and return JWT tokens."""
    existing_user_by_username = await get_user_by_username(user_in.username)
    if existing_user_by_username:
        raise HTTPException(status_code=400, detail="Username already registered")
    created_user = await create_user(
        db=db, user_in=user_in
    )
    return create_tokens(
        created_user["username"]
        if isinstance(created_user, dict)
        else created_user.username
    )


@router.post("/token", response_model=Token, summary="Login to get access token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 compatible token login, get an access token for future requests."""
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return create_tokens(form_data.username)


@router.post("/token/refresh", response_model=Token, summary="Refresh access token")
async def refresh_token(refresh_token: RefreshToken):
    """Refresh access token using a valid refresh token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            refresh_token.refresh_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        username: str | None = payload.get("sub")
        is_refresh = payload.get("refresh", False)
        if username is None or not is_refresh:
            raise credentials_exception
        return create_tokens(username)
    except InvalidTokenError as e:
        raise credentials_exception from e