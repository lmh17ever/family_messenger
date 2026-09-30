from redis.asyncio import Redis
import asyncio
from contextlib import suppress
import json
from sqlalchemy import select, func
from redis.asyncio.client import PubSub

from app.core.config import settings
from app.models.chat import ChatMember
from app.models.message import Message


class RedisManager:
    def __init__(self) -> None:
        self._client = Redis.from_url(settings.REDIS_URL, decode_responses=True)


    def pubsub(self) -> PubSub:
        return self._client.pubsub()

    async def close(self) -> None:
        await self._client.aclose()

    async def publish(self, channel_name: str, payload: dict) -> None:
        await self._client.publish(channel_name, json.dumps(payload))

    async def pipe_publish(self, events: list[tuple[str, str]]) -> None:
        """
        Bulk publish data to multiple channels using a non-transactional pipeline.
        Accepts a list of pairs: [("channel_name (string)", "payload (json_string)"), ...]
        """
        async with self._client.pipeline(transaction=False) as pipe:
            for channel, payload in events:
                pipe.publish(channel, payload)
            await pipe.execute()

redis_manager = RedisManager()
