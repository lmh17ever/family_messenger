from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.attachment import AttachmentOut
from app.schemas.user import UserOut


class MessageCreate(BaseModel):
    text: str | None = Field(default=None, max_length=10_000)
    attachment_ids: list[int] = Field(default_factory=list)


class MessageUpdate(BaseModel):
    text: str | None = Field(default=None, max_length=10_000)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # обязательно для ORM-объектов

    id: int
    chat_id: int
    sender_id: int | None
    text: str | None
    created_at: datetime
    sender: UserOut | None = None
    attachments: list[AttachmentOut] = Field(default_factory=list)
