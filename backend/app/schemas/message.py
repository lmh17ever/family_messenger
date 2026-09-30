from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator

from app.schemas.attachment import AttachmentOut
from app.schemas.user import UserOut


class MessageCreate(BaseModel):
    text: str | None = Field(default=None, max_length=10_000)
    attachment_ids: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_not_empty(self) -> "MessageCreate":
        if not self.text and not self.attachment_ids:
            raise ValueError("Message must have text or at least one attachment")
        return self

    @field_validator("text")
    @classmethod
    def empty_str_to_none(cls, string: str | None) -> str | None:
        if string is not None:
            string = string.strip()
            if not string:
                return None
        return string

    @field_validator("attachment_ids")
    @classmethod
    def unique_ids(cls, attachment_ids: list[int]) -> list[int]:
        if len(set(attachment_ids)) != len(attachment_ids):
            raise ValueError("attachment_ids must not contain duplicates")
        return attachment_ids


class MessageUpdate(BaseModel):
    text: str = Field(max_length=10_000)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chat_id: int
    sender_id: int | None
    text: str | None
    created_at: datetime
    sender: UserOut | None = None
    attachments: list[AttachmentOut] = Field(default_factory=list)
