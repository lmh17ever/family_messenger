from pydantic import BaseModel, Field


class PresignRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=128)
    size: int = Field(gt=0)


class AvatarConfirmIn(BaseModel):
    avatar_key: str = Field(min_length=1, max_length=1024)


class PresignOut(BaseModel):
    attachment_id: int
    upload: dict   # {"url": ..., "fields": {...}}
