# routers/attachments.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.session import get_session
from app.api.dependencies.chat import get_chat_as_member
from app.core.security import get_current_user
from app.models.chat import Chat
from app.models.user import User
from app.models.attachment import Attachment
from app.schemas.storage import PresignOut, PresignRequest
from app.schemas.attachment import AttachmentOut
from app.services.attachments import AttachmentForbidden, AttachmentInvalid, AttachmentNotFound, confirm_attachment, create_attachment_presign, get_attachment_download_url


router = APIRouter()

@router.post("/chats/{chat_id}/attachments/presign", response_model=PresignOut, status_code=201)
async def presign_attachment(
    body: PresignRequest,
    chat: Chat = Depends(get_chat_as_member),
    db: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    try:
        att, upload = await create_attachment_presign(db, chat, user, body)
    except AttachmentInvalid as e:
        raise HTTPException(422, str(e))
    return PresignOut(attachment_id=att.id, upload=upload)


@router.get("/attachments/{attachment_id}/url")
async def get_attachment_url(
    attachment_id: int,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    try:
        url = await get_attachment_download_url(db, attachment_id, user.id)
    except AttachmentNotFound:
        raise HTTPException(404)
    except AttachmentForbidden:
        raise HTTPException(404)
    return {"url": url}

@router.post("/attachments/{attachment_id}/confirm", response_model=AttachmentOut)
async def confirm_attachment_endpoint(
    attachment_id: int,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    attachment = await db.get(Attachment, attachment_id)

    if attachment is None:
        raise HTTPException(404, "Attachment not found")

    if attachment.uploader_id != user.id:
        raise HTTPException(403, "Forbidden")

    try:
        attachment = await confirm_attachment(db, attachment)
    except AttachmentInvalid as e:
        raise HTTPException(400, str(e))

    return attachment
