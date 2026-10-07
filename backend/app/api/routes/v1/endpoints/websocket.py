import asyncio
import json
from contextlib import suppress

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.session import get_session
from app.core.config import settings
from app.models.chat import Chat
from app.models.user import User
from app.schemas.message import MessageCreate
from app.core.security import jwt
from app.crud.message import create_message
from app.services.message import message_to_out
from app.services.chat import is_chat_member
from redis.asyncio import Redis
from app.api.dependencies.realtime import get_websocket_user
from app.core.realtime.websocket_manager import websocket_manager
from app.core.realtime.redis_manager import redis_manager
from app.services.realtime.event_service import event_service


router = APIRouter(tags=["realtime"])


@router.websocket("/chats/{chat_id}/ws")
async def chat_websocket(
    websocket: WebSocket,
    chat_id: int,
    db: AsyncSession = Depends(get_session),
    user: User | None = Depends(get_websocket_user),
) -> None:
    if user is None:
        await websocket.close(code=1008, reason="Authentication required")
        return

    if not await is_chat_member(db, chat_id, user.id):
        await websocket.close(code=1008, reason="Chat membership required")
        return

    await websocket_manager.connect(
        event_service.generate_chat_channel_name(chat_id),
        websocket)
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
                await websocket.send_json({"type": "error", "detail": error.errors(include_context=False)})
                continue
            chat = await db.get(Chat, chat_id)
            if chat is None:
                await websocket.send_json({"type": "error", "detail": "Chat not found"})
                continue
            message = await create_message(db, chat, user.id, message_in)
            payload = message_to_out(message)
            payload_data = payload.model_dump(mode="json")
            await redis_manager.publish(
                event_service.generate_chat_channel_name(chat_id),
                {"type": "message.created", "message": payload_data},
            )
            await event_service.broadcast_chat_users(
                db, chat_id, {"type": "chat.updated", "chat_id": chat_id}
            )
            await event_service.notify_new_message(
                db, chat_id, payload_data, user.id
            )
    except WebSocketDisconnect:
        pass
    finally:
        await websocket_manager.disconnect(event_service.generate_chat_channel_name(chat_id), websocket)


@router.websocket("/users/me/ws")
async def user_websocket(websocket: WebSocket, user: User | None = Depends(get_websocket_user)) -> None:
    if user is None:
        await websocket.close(code=1008, reason="Authentication required")
        return

    await websocket_manager.connect(
        event_service.generate_user_channel_name(user.id),
        websocket
    )
    try:
        await websocket.send_json({"type": "connected"})
        while True:
            event = await websocket.receive_json()
            event_type = event.get("type")

            if event_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            await websocket.send_json({
                "type": "error",
                "detail": f"Unknown event type: {event_type}"
            })

    except WebSocketDisconnect:
        pass
    finally:
        await websocket_manager.disconnect(event_service.generate_user_channel_name(user.id), websocket)
