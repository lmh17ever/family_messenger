from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlalchemy import select

from app.api.dependencies.session import AsyncSessionLocal
from app.core.config import settings
from app.models.chat import Chat, ChatMember
from app.models.user import User
from app.schemas.message import MessageCreate
from app.core.security import jwt
from app.crud.message import create_message
from app.services.message import message_to_out
from app.services.realtime import chat_connections


router = APIRouter(tags=["realtime"])


async def get_websocket_user(websocket: WebSocket) -> User | None:
    token = websocket.query_params.get("token")
    authorization = websocket.headers.get("authorization", "")
    if not token and authorization.lower().startswith("bearer "):
        token = authorization[7:]
    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        username = payload.get("sub")
        if not username or payload.get("refresh", False):
            return None
    except InvalidTokenError:
        return None

    async with AsyncSessionLocal() as db:
        return await db.scalar(select(User).where(User.username == username))


async def is_member(db, chat_id: int, user_id: int) -> bool:
    return (
        await db.scalar(
            select(ChatMember.chat_id).where(
                ChatMember.chat_id == chat_id,
                ChatMember.user_id == user_id,
            )
        )
    ) is not None


@router.websocket("/chats/{chat_id}/ws")
async def chat_websocket(websocket: WebSocket, chat_id: int) -> None:
    user = await get_websocket_user(websocket)
    if user is None:
        await websocket.close(code=1008, reason="Authentication required")
        return

    async with AsyncSessionLocal() as db:
        if not await is_member(db, chat_id, user.id):
            await websocket.close(code=1008, reason="Chat membership required")
            return

    await chat_connections.connect(chat_id, websocket)
    try:
        await websocket.send_json({"type": "connected", "chat_id": chat_id})
        while True:
            event = await websocket.receive_json()
            event_type = event.get("type")

            if event_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if event_type != "send_message":
                await websocket.send_json({"type": "error", "detail": "Unknown event type"})
                continue

            try:
                message_in = MessageCreate.model_validate(event.get("message", {}))
            except ValidationError as error:
                await websocket.send_json({"type": "error", "detail": error.errors()})
                continue
            async with AsyncSessionLocal() as db:
                chat = await db.get(Chat, chat_id)
                if chat is None:
                    await websocket.send_json({"type": "error", "detail": "Chat not found"})
                    continue
                message = await create_message(db, chat, user.id, message_in)
                payload = await message_to_out(message)

            await chat_connections.broadcast(
                chat_id,
                {"type": "message.created", "message": payload.model_dump(mode="json")},
            )
    except WebSocketDisconnect:
        pass
    finally:
        await chat_connections.disconnect(chat_id, websocket)
