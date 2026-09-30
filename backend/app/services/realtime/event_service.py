from redis.asyncio import Redis
import asyncio
from contextlib import suppress
import json
from sqlalchemy import select, func
from redis.asyncio.client import PubSub

from app.core.config import settings
from app.models.chat import ChatMember
from app.models.message import Message
from app.core.realtime.redis_manager import redis_manager


class EventService:
    def generate_chat_channel_name(self, chat_id: int) -> str:
        return f"chat:{chat_id}"

    def generate_user_channel_name(self, user_id: int) -> str:
        return f"user:{user_id}"

    async def broadcast_chat_users(
        self,
        db,
        chat_id: int,
        payload: dict,
        exclude_user_id: int | None = None,
    ) -> None:
        stmt = select(ChatMember.user_id).where(ChatMember.chat_id == chat_id)
        if exclude_user_id is not None:
            stmt = stmt.where(ChatMember.user_id != exclude_user_id)
        user_ids = await db.scalars(stmt)
        serialized_payload = json.dumps(payload)
        events = []
        for user_id in user_ids:
            events.append((self.generate_user_channel_name(user_id), serialized_payload))
        await redis_manager.pipe_publish(events)

    async def notify_new_message(
        self,
        db,
        chat_id: int,
        message: dict,
        sender_id: int,
    ) -> None:
        stmt = (
            select(ChatMember.user_id, func.count(Message.id).label("unread_count"))
            .outerjoin(
                Message,
                (Message.chat_id == ChatMember.chat_id) &
                (Message.id > func.coalesce(ChatMember.last_read_message_id, 0))
            )
            .where(ChatMember.chat_id == chat_id, ChatMember.user_id != sender_id)
            .group_by(ChatMember.user_id)
        )
        result = await db.execute(stmt)
        events = []
        for user_id, unread_count in result.all():
            payload = {
                "type": "notification.new_message",
                "chat_id": chat_id,
                "message_id": message["id"],
                "sender_id": sender_id,
                "sender": message.get("sender"),
                "text": message.get("text"),
                "created_at": message.get("created_at"),
                "unread_count": unread_count or 0,
            }
            events.append((self.generate_user_channel_name(user_id), json.dumps(payload)))
        await redis_manager.pipe_publish(events)

event_service = EventService()
