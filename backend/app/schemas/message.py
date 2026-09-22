from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MessageCreate(BaseModel):
    text: str | None = Field(default=None, max_length=10_000)
    attachment_ids: list[int] = Field(default_factory=list)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # обязательно для ORM-объектов

    id: int
    chat_id: int
    sender_id: int | None
    text: str | None
    created_at: datetime
