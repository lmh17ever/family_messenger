from typing import Literal

from pydantic import BaseModel, Field

# To protect API
PASSWORD_LENGTH = 72


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"


class TokenData(BaseModel):
    """Schema for data encoded within a JWT token."""

    user_id: int = Field(gt=0)


class UserLogin(BaseModel):
    """Schema for user login request."""

    username: str
    password: str = Field(max_length=PASSWORD_LENGTH)


class RefreshToken(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str
