from pydantic import BaseModel, Field
from app.core.config import settings
from app.models.attachment import FILENAME_LEGNTH, CONTENT_TYPE_LENGHT
from app.models.user import AVATAR_KEY_LENGTH


class PresignRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=FILENAME_LEGNTH)
    content_type: str = Field(min_length=1, max_length=CONTENT_TYPE_LENGHT)
    size: int = Field(gt=0, le=settings.MAX_ATTACHMENT_SIZE)


class AvatarConfirmIn(BaseModel):
    avatar_key: str = Field(min_length=1, max_length=AVATAR_KEY_LENGTH)


class PresignedUpload(BaseModel):
    url: str
    fields: dict


class PresignOut(BaseModel):
    attachment_id: int
    upload: dict
