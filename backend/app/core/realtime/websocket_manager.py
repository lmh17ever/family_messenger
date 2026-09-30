import asyncio
import json
from collections import defaultdict
from contextlib import suppress
from websockets.exceptions import ConnectionClosed, WebSocketException

from fastapi import WebSocket

from app.core.realtime.redis_manager import redis_manager


class WebSocketManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._listeners: dict[str, asyncio.Task[None]] = {}

    async def connect(self, channel_name: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[channel_name].add(websocket)
        if channel_name not in self._listeners:
            self._listeners[channel_name] = asyncio.create_task(self._listen(channel_name))

    async def disconnect(self, channel_name: str, websocket: WebSocket) -> None:
        connections = self._connections.get(channel_name)
        if connections is None:
            return
        connections.discard(websocket)
        if not connections:
            self._connections.pop(channel_name, None)
            listener = self._listeners.pop(channel_name, None)
            if listener is not None and listener is not asyncio.current_task():
                listener.cancel()
                with suppress(asyncio.CancelledError):
                    await listener

    async def close(self) -> None:
        for listener in list(self._listeners.values()):
            listener.cancel()
        for listener in list(self._listeners.values()):
            with suppress(asyncio.CancelledError):
                await listener
        self._listeners.clear()
        await redis_manager.close()

    async def _listen(self, channel_name: str) -> None:
        pubsub = redis_manager.pubsub()
        await pubsub.subscribe(channel_name)
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
                for websocket in self._connections.get(channel_name, set()).copy():
                    try:
                        await websocket.send_json(payload)
                    except (ConnectionClosed, WebSocketException, RuntimeError):
                        disconnected.append(websocket)
                for websocket in disconnected:
                    await self.disconnect(channel_name, websocket)
        finally:
            await pubsub.unsubscribe(channel_name)
            await pubsub.aclose()

websocket_manager = WebSocketManager()
