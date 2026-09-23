import asyncio
import json
from contextlib import suppress

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
from redis.asyncio import Redis


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
                payload_data = payload.model_dump(mode="json")
                await chat_connections.broadcast(
                    chat_id,
                    {"type": "message.created", "message": payload_data},
                )
                await chat_connections.broadcast_chat_users(
                    db, chat_id, {"type": "chat.updated", "chat_id": chat_id}
                )
                await chat_connections.notify_new_message(
                    db, chat_id, payload_data, user.id
                )
    except WebSocketDisconnect:
        pass
    finally:
        await chat_connections.disconnect(chat_id, websocket)


@router.websocket("/users/me/ws")
async def user_websocket(websocket: WebSocket) -> None:
    user = await get_websocket_user(websocket)
    if user is None:
        await websocket.close(code=1008, reason="Authentication required")
        return

    await websocket.accept()
    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = redis.pubsub()
    channel = f"user:{user.id}"
    await pubsub.subscribe(channel)
    try:
        await websocket.send_json({"type": "connected"})
        while True:
            receive_task = asyncio.create_task(websocket.receive())
            redis_task = asyncio.create_task(
                pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            )
            done, pending = await asyncio.wait(
                {receive_task, redis_task},
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
            if redis_task in done:
                event = redis_task.result()
                if event is not None:
                    await websocket.send_json(json.loads(event["data"]))
            if receive_task in done:
                message = receive_task.result()

                if message["type"] == "websocket.disconnect":
                    break
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()
        await redis.aclose()
