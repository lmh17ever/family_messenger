"""WebSocket tests: auth, ping/pong, message flow over realtime."""

from __future__ import annotations

import time

import pytest
from starlette.websockets import WebSocketDisconnect

from utils import auth_headers, get_me_id, open_direct_chat, register

# The WS listener subscribes to Redis asynchronously after accept; give it a
# moment before publishing events that must be delivered back over the socket.
SUBSCRIPTION_GRACE = 0.5


class TestUserWebsocket:
    def test_no_token_rejected(self, client):
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect("/api/v1/users/me/ws"):
                pass
        assert exc_info.value.code == 1008

    def test_invalid_token_rejected(self, client):
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect("/api/v1/users/me/ws?token=garbage"):
                pass
        assert exc_info.value.code == 1008

    def test_refresh_token_rejected(self, client):
        tokens = register(client, "alice")
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect(
                f"/api/v1/users/me/ws?token={tokens['refresh_token']}"
            ):
                pass
        assert exc_info.value.code == 1008

    def test_connect_and_ping(self, client):
        tokens = register(client, "alice")
        with client.websocket_connect(
            f"/api/v1/users/me/ws?token={tokens['access_token']}"
        ) as ws:
            assert ws.receive_json() == {"type": "connected"}
            ws.send_json({"type": "ping"})
            assert ws.receive_json() == {"type": "pong"}

    def test_unknown_event_type_error(self, client):
        tokens = register(client, "alice")
        with client.websocket_connect(
            f"/api/v1/users/me/ws?token={tokens['access_token']}"
        ) as ws:
            assert ws.receive_json() == {"type": "connected"}
            ws.send_json({"type": "mystery"})
            resp = ws.receive_json()
            assert resp["type"] == "error"
            assert "mystery" in resp["detail"]


class TestChatWebsocket:
    def test_no_token_rejected(self, client):
        alice = register(client, "alice")
        bob = register(client, "bob")
        chat = open_direct_chat(client, alice, get_me_id(client, bob))
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect(f"/api/v1/chats/{chat['id']}/ws"):
                pass
        assert exc_info.value.code == 1008

    def test_non_member_rejected(self, client):
        alice = register(client, "alice")
        bob = register(client, "bob")
        carol = register(client, "carol")
        chat = open_direct_chat(client, alice, get_me_id(client, bob))
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect(
                f"/api/v1/chats/{chat['id']}/ws?token={carol['access_token']}"
            ):
                pass
        assert exc_info.value.code == 1008

    def test_member_connects_and_pings(self, client):
        alice = register(client, "alice")
        bob = register(client, "bob")
        chat = open_direct_chat(client, alice, get_me_id(client, bob))
        with client.websocket_connect(
            f"/api/v1/chats/{chat['id']}/ws?token={alice['access_token']}"
        ) as ws:
            connected = ws.receive_json()
            assert connected == {"type": "connected", "chat_id": chat["id"]}
            ws.send_json({"type": "ping"})
            assert ws.receive_json() == {"type": "pong"}

    def test_unknown_event_type_error(self, client):
        alice = register(client, "alice")
        bob = register(client, "bob")
        chat = open_direct_chat(client, alice, get_me_id(client, bob))
        with client.websocket_connect(
            f"/api/v1/chats/{chat['id']}/ws?token={alice['access_token']}"
        ) as ws:
            ws.receive_json()  # connected
            ws.send_json({"type": "nonsense"})
            resp = ws.receive_json()
            assert resp["type"] == "error"
            assert resp["detail"] == "Unknown event type"



class TestRealtimeMessageFlow:
    def test_send_message_over_ws(self, client):
        """A message sent through the socket is persisted and broadcast back."""
        alice = register(client, "alice")
        bob = register(client, "bob")
        chat = open_direct_chat(client, alice, get_me_id(client, bob))
        with client.websocket_connect(
            f"/api/v1/chats/{chat['id']}/ws?token={alice['access_token']}"
        ) as ws:
            ws.receive_json()  # connected
            time.sleep(SUBSCRIPTION_GRACE)
            ws.send_json({"type": "send_message", "message": {"text": "over ws"}})
            event = ws.receive_json()
            assert event["type"] == "message.created"
            assert event["message"]["text"] == "over ws"

        # The message was persisted.
        resp = client.get(
            f"/api/v1/chats/{chat['id']}/messages", headers=auth_headers(alice)
        )
        assert [m["text"] for m in resp.json()] == ["over ws"]

    def test_send_message_over_ws_validation_error(self, client):
        alice = register(client, "alice")
        bob = register(client, "bob")
        chat = open_direct_chat(client, alice, get_me_id(client, bob))
        with client.websocket_connect(
            f"/api/v1/chats/{chat['id']}/ws?token={alice['access_token']}"
        ) as ws:
            ws.receive_json()  # connected
            ws.send_json({"type": "send_message", "message": {}})
            resp = ws.receive_json()
            assert resp["type"] == "error"
        # Nothing was persisted.
        resp = client.get(
            f"/api/v1/chats/{chat['id']}/messages", headers=auth_headers(alice)
        )
        assert resp.json() == []

    def test_http_message_reaches_chat_socket(self, client):
        """An HTTP-created message is pushed to a listening chat socket."""
        alice = register(client, "alice")
        bob = register(client, "bob")
        chat = open_direct_chat(client, alice, get_me_id(client, bob))
        with client.websocket_connect(
            f"/api/v1/chats/{chat['id']}/ws?token={alice['access_token']}"
        ) as ws:
            ws.receive_json()  # connected
            time.sleep(SUBSCRIPTION_GRACE)
            # Bob posts over HTTP while Alice listens.
            resp = client.post(
                f"/api/v1/chats/{chat['id']}/messages",
                headers=auth_headers(bob),
                json={"text": "from http"},
            )
            assert resp.status_code == 200
            event = ws.receive_json()
            assert event["type"] == "message.created"
            assert event["message"]["text"] == "from http"

    def test_user_socket_receives_notification(self, client):
        """Bob's user socket gets chat.updated + notification.new_message."""
        alice = register(client, "alice")
        bob = register(client, "bob")
        chat = open_direct_chat(client, alice, get_me_id(client, bob))
        with client.websocket_connect(
            f"/api/v1/users/me/ws?token={bob['access_token']}"
        ) as ws:
            assert ws.receive_json() == {"type": "connected"}
            time.sleep(SUBSCRIPTION_GRACE)
            resp = client.post(
                f"/api/v1/chats/{chat['id']}/messages",
                headers=auth_headers(alice),
                json={"text": "ping bob"},
            )
            assert resp.status_code == 200
            first = ws.receive_json()
            second = ws.receive_json()
            assert first["type"] == "chat.updated"
            assert first["chat_id"] == chat["id"]
            assert second["type"] == "notification.new_message"
            assert second["text"] == "ping bob"
            assert second["unread_count"] == 1

