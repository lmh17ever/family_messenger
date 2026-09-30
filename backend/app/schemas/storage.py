from pydantic import BaseModel, Field
from app.core.config import settings


class PresignRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=128)
    size: int = Field(gt=0, le=settings.MAX_ATTACHMENT_SIZE)


class AvatarConfirmIn(BaseModel):
    avatar_key: str = Field(min_length=1, max_length=1024)


class PresignedUpload(BaseModel):
    url: str
    fields: dict


class PresignOut(BaseModel):
    attachment_id: int
    upload: dict
