import asyncio
import json
from collections import defaultdict
from contextlib import suppress

from fastapi import WebSocket
from redis.asyncio import Redis

from app.core.config import settings


class ChatConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)
        self._listeners: dict[int, asyncio.Task[None]] = {}
        self._redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def connect(self, chat_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[chat_id].add(websocket)
        if chat_id not in self._listeners:
            self._listeners[chat_id] = asyncio.create_task(self._listen(chat_id))

    async def disconnect(self, chat_id: int, websocket: WebSocket) -> None:
        connections = self._connections.get(chat_id)
        if connections is None:
            return
        connections.discard(websocket)
        if not connections:
            self._connections.pop(chat_id, None)
            listener = self._listeners.pop(chat_id, None)
            if listener is not None and listener is not asyncio.current_task():
                listener.cancel()
                with suppress(asyncio.CancelledError):
                    await listener

    async def broadcast(self, chat_id: int, payload: dict) -> None:
        await self._redis.publish(self._channel(chat_id), json.dumps(payload))

    async def broadcast_user(self, user_id: int, payload: dict) -> None:
        await self._redis.publish(self._user_channel(user_id), json.dumps(payload))

    async def broadcast_chat_users(self, db, chat_id: int, payload: dict) -> None:
        await self.broadcast_chat_users_except(db, chat_id, payload)

    async def broadcast_chat_users_except(
        self,
        db,
        chat_id: int,
        payload: dict,
        exclude_user_id: int | None = None,
    ) -> None:
        from sqlalchemy import select
        from app.models.chat import ChatMember

        stmt = select(ChatMember.user_id).where(ChatMember.chat_id == chat_id)
        if exclude_user_id is not None:
            stmt = stmt.where(ChatMember.user_id != exclude_user_id)
        user_ids = await db.scalars(stmt)
        for user_id in user_ids:
            await self.broadcast_user(user_id, payload)

    async def notify_new_message(
        self,
        db,
        chat_id: int,
        message: dict,
        sender_id: int,
    ) -> None:
        from sqlalchemy import func, select
        from app.models.chat import ChatMember
        from app.models.message import Message

        members = await db.scalars(
            select(ChatMember).where(ChatMember.chat_id == chat_id)
        )
        for member in members:
            if member.user_id == sender_id:
                continue
            unread_count = await db.scalar(
                select(func.count(Message.id)).where(
                    Message.chat_id == chat_id,
                    Message.id > (member.last_read_message_id or 0),
                )
            ) or 0
            await self.broadcast_user(
                member.user_id,
                {
                    "type": "notification.new_message",
                    "chat_id": chat_id,
                    "message_id": message["id"],
                    "sender_id": sender_id,
                    "sender": message.get("sender"),
                    "text": message.get("text"),
                    "created_at": message.get("created_at"),
                    "unread_count": unread_count,
                },
            )

    async def close(self) -> None:
        for listener in list(self._listeners.values()):
            listener.cancel()
        for listener in list(self._listeners.values()):
            with suppress(asyncio.CancelledError):
                await listener
        self._listeners.clear()
        await self._redis.aclose()

    @staticmethod
    def _channel(chat_id: int) -> str:
        return f"chat:{chat_id}"

    @staticmethod
    def _user_channel(user_id: int) -> str:
        return f"user:{user_id}"

    async def _listen(self, chat_id: int) -> None:
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(self._channel(chat_id))
        try:
            while True:
                event = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )
                if event is None:
                    continue
                payload = json.loads(event["data"])
                disconnected: list[WebSocket] = []
                for websocket in self._connections.get(chat_id, set()).copy():
                    try:
                        await websocket.send_json(payload)
                    except Exception:
                        disconnected.append(websocket)
                for websocket in disconnected:
                    await self.disconnect(chat_id, websocket)
        finally:
            await pubsub.unsubscribe(self._channel(chat_id))
            await pubsub.aclose()


chat_connections = ChatConnectionManager()
