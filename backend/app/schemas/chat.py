from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.chat import ChatType


class ChatBase(BaseModel):
    pass


class ChatCreate(ChatBase):
    user1_id: int
    user2_id: int


class ChatOut(ChatBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: ChatType
    title: str | None = None
    avatar_key: str | None = None
    created_at: datetime
    last_message_at: datetime | None = None
