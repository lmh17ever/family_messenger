from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash


from app.core.config import settings
from app.services.user import get_user_by_username
from app.api.dependencies.session import get_session

from app.schemas.token import TokenData


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


async def authenticate_user(username: str, password: str, db: AsyncSession):
    user = await get_user_by_username(username, db)
    if not user or not user.hashed_password:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode.update({"exp": expire, "refresh": True})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_tokens(username: str):
    """Create both access and refresh tokens for a user."""
    access_token = create_access_token({"sub": username})
    refresh_token = create_refresh_token({"sub": username})
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
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None or payload.get("refresh", False):
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError as e:
        raise credentials_exception from e

    user = await get_user_by_username(username=token_data.username, db=db) # type: ignore
    if user is None:
        raise credentials_exception
    return user
