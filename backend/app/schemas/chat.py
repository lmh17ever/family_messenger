from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.chat import ChatType
from app.schemas.message import MessageOut
from app.schemas.user import UserOut
from app.models.user import AVATAR_KEY_LENGTH
from app.models.attachment import CONTENT_TYPE_LENGHT


class ChatBase(BaseModel):
    pass


class ChatCreate(ChatBase):
    target_user_id: int


class ChatOut(ChatBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: ChatType
    creator_id: int | None = None
    title: str | None = None
    avatar_key: str | None = None
    avatar_url: str | None = None
    created_at: datetime
    last_message_at: datetime | None = None
    participants: list[UserOut] = Field(default_factory=list)
    last_message: MessageOut | None = None
    unread_count: int = 0


class GroupChatCreate(BaseModel):
    title: str
    member_ids: list[int] = Field(default_factory=list)


class ChatReadIn(BaseModel):
    message_id: int | None = None


class ChatAvatarConfirmIn(BaseModel):
    avatar_key: str = Field(min_length=1, max_length=AVATAR_KEY_LENGTH)


class ChatAvatarPresignIn(BaseModel):
    content_type: str = Field(min_length=1, max_length=CONTENT_TYPE_LENGHT)
    size: int = Field(gt=0)


class ChatMemberIn(BaseModel):
    user_id: int
