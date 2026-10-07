"""Message endpoint tests: create/list/search/edit/delete."""

from __future__ import annotations

from utils import auth_headers, get_me_id, open_direct_chat, register, send_message


def _setup(client):
    """Two users and their direct chat."""
    alice = register(client, "alice")
    bob = register(client, "bob")
    chat = open_direct_chat(client, alice, get_me_id(client, bob))
    return alice, bob, chat


class TestCreateMessage:
    def test_create_message(self, client):
        alice, _bob, chat = _setup(client)
        resp = client.post(
            f"/api/v1/chats/{chat['id']}/messages",
            headers=auth_headers(alice),
            json={"text": "hello"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["text"] == "hello"
        assert body["chat_id"] == chat["id"]
        assert body["sender"]["username"] == "alice"

    def test_empty_message_rejected(self, client):
        alice, _bob, chat = _setup(client)
        resp = client.post(
            f"/api/v1/chats/{chat['id']}/messages",
            headers=auth_headers(alice),
            json={"text": ""},
        )
        assert resp.status_code == 422

    def test_non_member_cannot_post(self, client):
        alice, _bob, chat = _setup(client)
        carol = register(client, "carol")
        resp = client.post(
            f"/api/v1/chats/{chat['id']}/messages",
            headers=auth_headers(carol),
            json={"text": "hi"},
        )
        assert resp.status_code == 404

    def test_requires_auth(self, client):
        alice, _bob, chat = _setup(client)
        resp = client.post(
            f"/api/v1/chats/{chat['id']}/messages", json={"text": "hi"}
        )
        assert resp.status_code == 401


class TestListMessages:
    def test_list_newest_first(self, client):
        alice, _bob, chat = _setup(client)
        for i in range(3):
            send_message(client, alice, chat["id"], f"msg {i}")
        resp = client.get(
            f"/api/v1/chats/{chat['id']}/messages", headers=auth_headers(alice)
        )
        assert resp.status_code == 200
        texts = [m["text"] for m in resp.json()]
        assert texts == ["msg 2", "msg 1", "msg 0"]

    def test_pagination_before_id(self, client):
        alice, _bob, chat = _setup(client)
        ids = [
            send_message(client, alice, chat["id"], f"msg {i}")["id"]
            for i in range(3)
        ]
        resp = client.get(
            f"/api/v1/chats/{chat['id']}/messages",
            params={"before_id": ids[1], "limit": 10},
            headers=auth_headers(alice),
        )
        assert [m["id"] for m in resp.json()] == [ids[0]]

    def test_search(self, client):
        alice, _bob, chat = _setup(client)
        send_message(client, alice, chat["id"], "hello world")
        send_message(client, alice, chat["id"], "goodbye")
        resp = client.get(
            f"/api/v1/chats/{chat['id']}/messages",
            params={"search": "HELLO"},
            headers=auth_headers(alice),
        )
        assert [m["text"] for m in resp.json()] == ["hello world"]

    def test_non_member_cannot_list(self, client):
        alice, _bob, chat = _setup(client)
        carol = register(client, "carol")
        resp = client.get(
            f"/api/v1/chats/{chat['id']}/messages", headers=auth_headers(carol)
        )
        assert resp.status_code == 404



class TestEditMessage:
    def test_author_can_edit(self, client):
        alice, _bob, chat = _setup(client)
        msg = send_message(client, alice, chat["id"], "original")
        resp = client.patch(
            f"/api/v1/chats/{chat['id']}/messages/{msg['id']}",
            headers=auth_headers(alice),
            json={"text": "edited"},
        )
        assert resp.status_code == 200
        assert resp.json()["text"] == "edited"

    def test_other_member_cannot_edit(self, client):
        alice, bob, chat = _setup(client)
        msg = send_message(client, alice, chat["id"], "original")
        resp = client.patch(
            f"/api/v1/chats/{chat['id']}/messages/{msg['id']}",
            headers=auth_headers(bob),
            json={"text": "hacked"},
        )
        assert resp.status_code == 404

    def test_edit_missing_message_404(self, client):
        alice, _bob, chat = _setup(client)
        resp = client.patch(
            f"/api/v1/chats/{chat['id']}/messages/999999",
            headers=auth_headers(alice),
            json={"text": "x"},
        )
        assert resp.status_code == 404


class TestDeleteMessage:
    def test_author_can_delete(self, client):
        alice, _bob, chat = _setup(client)
        msg = send_message(client, alice, chat["id"], "bye")
        resp = client.delete(
            f"/api/v1/chats/{chat['id']}/messages/{msg['id']}",
            headers=auth_headers(alice),
        )
        assert resp.status_code == 204
        resp = client.get(
            f"/api/v1/chats/{chat['id']}/messages", headers=auth_headers(alice)
        )
        assert resp.json() == []

    def test_other_member_cannot_delete(self, client):
        alice, bob, chat = _setup(client)
        msg = send_message(client, alice, chat["id"], "keep me")
        resp = client.delete(
            f"/api/v1/chats/{chat['id']}/messages/{msg['id']}",
            headers=auth_headers(bob),
        )
        assert resp.status_code == 404

    def test_delete_last_message_resets_chat_last_message(self, client):
        alice, _bob, chat = _setup(client)
        first = send_message(client, alice, chat["id"], "first")
        second = send_message(client, alice, chat["id"], "second")
        resp = client.delete(
            f"/api/v1/chats/{chat['id']}/messages/{second['id']}",
            headers=auth_headers(alice),
        )
        assert resp.status_code == 204
        # Chat now points back at the previous message.
        resp = client.get(f"/api/v1/chats/{chat['id']}", headers=auth_headers(alice))
        assert resp.json()["last_message"]["id"] == first["id"]

