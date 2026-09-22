from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings
from app.models.user import User


class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=30)


class UserCreate(UserBase):
    password: str = Field(min_length=1)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    avatar_url: str | None = None

    @classmethod
    def from_user(cls, user: "User") -> "UserOut":
        return cls(
            id=user.id,
            username=user.username,
            avatar_url=f"{settings.S3_BASE_URL}/{settings.S3_PUBLIC_BUCKET}/{user.avatar_key}" if user.avatar_key else None,
        )
