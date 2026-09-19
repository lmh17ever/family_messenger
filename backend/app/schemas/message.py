from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MessageBase(BaseModel):
    chat_id: int
    sender_id: int
    text: str


class CreateMessage(MessageBase):
    pass


class MessageOut(MessageBase):
    model_config=ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
