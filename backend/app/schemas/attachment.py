from pydantic import BaseModel, ConfigDict


class AttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    filename: str
    content_type: str
    size: int
    url: str | None = None


class AvatarPresignOut(BaseModel):
    upload: dict
    avatar_key: str
