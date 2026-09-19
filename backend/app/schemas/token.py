from pydantic import BaseModel


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    """Schema for data encoded within a JWT token."""

    username: str | None = None


class UserLogin(BaseModel):
    """Schema for user login request."""

    username: str
    password: str


class RefreshToken(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str