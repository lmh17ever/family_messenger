from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from pwdlib import PasswordHash
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.session import get_session
from app.core.config import settings
from app.models.user import User
from app.schemas.token import TokenData
from app.services.user import get_user_by_id, get_user_by_username

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/token",
    scheme_name="OAuth2 password bearer",
    description="JWT token authorization",
)

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    user = await get_user_by_username(db, username)
    if not user or not user.hashed_password:
        return None
    if not await run_in_threadpool(verify_password, password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_ACCESS_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode.update({"exp": expire, "refresh": True})
    return jwt.encode(to_encode, settings.JWT_REFRESH_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_tokens(user_id: int):
    """Create both access and refresh tokens for a user."""
    subject = str(user_id)
    access_token = create_access_token({"sub": subject})
    refresh_token = create_refresh_token({"sub": subject})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_session),
):
    """Decode JWT token and retrieve the current user via repository."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_ACCESS_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        subject = payload.get("sub")
        if not isinstance(subject, str) or payload.get("refresh", False):
            raise credentials_exception
        token_data = TokenData.model_validate({"user_id": subject})
    except ValidationError as e:
        raise credentials_exception from e
    except InvalidTokenError as e:
        raise credentials_exception from e

    user = await get_user_by_id(db, token_data.user_id)
    if user is None:
        raise credentials_exception
    return user
