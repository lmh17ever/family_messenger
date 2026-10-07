"""Chat endpoint tests: direct/group chats, members, read state, avatars."""

from __future__ import annotations

from utils import auth_headers, get_me_id, open_direct_chat, register, send_message


def _create_group(client, creator_tokens: dict, title: str, member_ids: list[int]) -> dict:
    resp = client.post(
        "/api/v1/chats",
        headers=auth_headers(creator_tokens),
        json={"title": title, "member_ids": member_ids},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


class TestDirectChat:
    def test_open_direct_chat(self, client):
        alice = register(client, "alice")
        bob = register(client, "bob")
        chat = open_direct_chat(client, alice, get_me_id(client, bob))
        assert chat["type"] == "direct"
        assert {p["username"] for p in chat["participants"]} == {"alice", "bob"}

    def test_open_direct_chat_is_idempotent(self, client):
        alice = register(client, "alice")
        bob = register(client, "bob")
        bob_id = get_me_id(client, bob)
        first = open_direct_chat(client, alice, bob_id)
        second = open_direct_chat(client, alice, bob_id)
        assert first["id"] == second["id"]

    def test_direct_chat_symmetric(self, client):
        alice = register(client, "alice")
        bob = register(client, "bob")
        from_bob = open_direct_chat(client, bob, get_me_id(client, alice))
        from_alice = open_direct_chat(client, alice, get_me_id(client, bob))
        assert from_bob["id"] == from_alice["id"]


class TestGroupChat:
    def test_create_group_chat(self, client):
        alice = register(client, "alice")
        bob = register(client, "bob")
        chat = _create_group(client, alice, "Family", [get_me_id(client, bob)])
        assert chat["type"] == "group"
        assert chat["title"] == "Family"
        assert chat["creator_id"] == get_me_id(client, alice)
        assert {p["username"] for p in chat["participants"]} == {"alice", "bob"}

    def test_group_creator_not_duplicated(self, client):
        alice = register(client, "alice")
        alice_id = get_me_id(client, alice)
        chat = _create_group(client, alice, "Solo", [alice_id])
        # Creator listed in member_ids must not create duplicate rows.
        assert len(chat["participants"]) == 1


class TestMyChats:
    def test_my_chats_lists_direct_chat(self, client):
        alice = register(client, "alice")
        bob = register(client, "bob")
        chat = open_direct_chat(client, alice, get_me_id(client, bob))
        resp = client.get("/api/v1/chats/my", headers=auth_headers(alice))
        assert resp.status_code == 200
        assert [c["id"] for c in resp.json()] == [chat["id"]]

    def test_my_chats_excludes_non_member(self, client):
        alice = register(client, "alice")
        bob = register(client, "bob")
        carol = register(client, "carol")
        open_direct_chat(client, alice, get_me_id(client, bob))
        resp = client.get("/api/v1/chats/my", headers=auth_headers(carol))
        assert resp.json() == []

    def test_my_chats_requires_auth(self, client):
        assert client.get("/api/v1/chats/my").status_code == 401



class TestGetChat:
    def test_member_can_get_chat(self, client):
        alice = register(client, "alice")
        bob = register(client, "bob")
        chat = open_direct_chat(client, alice, get_me_id(client, bob))
        resp = client.get(f"/api/v1/chats/{chat['id']}", headers=auth_headers(alice))
        assert resp.status_code == 200

    def test_non_member_get_404(self, client):
        alice = register(client, "alice")
        bob = register(client, "bob")
        carol = register(client, "carol")
        chat = open_direct_chat(client, alice, get_me_id(client, bob))
        resp = client.get(f"/api/v1/chats/{chat['id']}", headers=auth_headers(carol))
        assert resp.status_code == 404

    def test_missing_chat_404(self, client):
        tokens = register(client, "alice")
        resp = client.get("/api/v1/chats/999999", headers=auth_headers(tokens))
        assert resp.status_code == 404


class TestMembers:
    def test_creator_can_add_member(self, client):
        alice = register(client, "alice")
        bob = register(client, "bob")
        carol = register(client, "carol")
        chat = _create_group(client, alice, "Family", [get_me_id(client, bob)])
        resp = client.post(
            f"/api/v1/chats/{chat['id']}/members",
            headers=auth_headers(alice),
            json={"user_id": get_me_id(client, carol)},
        )
        assert resp.status_code == 201

    def test_non_creator_cannot_add_member(self, client):
        alice = register(client, "alice")
        bob = register(client, "bob")
        carol = register(client, "carol")
        chat = _create_group(client, alice, "Family", [get_me_id(client, bob)])
        resp = client.post(
            f"/api/v1/chats/{chat['id']}/members",
            headers=auth_headers(bob),
            json={"user_id": get_me_id(client, carol)},
        )
        assert resp.status_code == 403

    def test_cannot_manage_members_of_direct_chat(self, client):
        alice = register(client, "alice")
        bob = register(client, "bob")
        carol = register(client, "carol")
        chat = open_direct_chat(client, alice, get_me_id(client, bob))
        resp = client.post(
            f"/api/v1/chats/{chat['id']}/members",
            headers=auth_headers(alice),
            json={"user_id": get_me_id(client, carol)},
        )
        assert resp.status_code == 403

    def test_non_member_cannot_add_member(self, client):
        alice = register(client, "alice")
        carol = register(client, "carol")
        chat = _create_group(client, alice, "Family", [])
        resp = client.post(
            f"/api/v1/chats/{chat['id']}/members",
            headers=auth_headers(carol),
            json={"user_id": get_me_id(client, carol)},
        )
        assert resp.status_code == 404



    def test_creator_can_remove_member(self, client):
        alice = register(client, "alice")
        bob = register(client, "bob")
        chat = _create_group(client, alice, "Family", [get_me_id(client, bob)])
        resp = client.delete(
            f"/api/v1/chats/{chat['id']}/members/{get_me_id(client, bob)}",
            headers=auth_headers(alice),
        )
        assert resp.status_code == 204
        # Removed member loses access.
        resp = client.get(f"/api/v1/chats/{chat['id']}", headers=auth_headers(bob))
        assert resp.status_code == 404

    def test_non_creator_cannot_remove_member(self, client):
        alice = register(client, "alice")
        bob = register(client, "bob")
        carol = register(client, "carol")
        chat = _create_group(
            client, alice, "Family", [get_me_id(client, bob), get_me_id(client, carol)]
        )
        resp = client.delete(
            f"/api/v1/chats/{chat['id']}/members/{get_me_id(client, carol)}",
            headers=auth_headers(bob),
        )
        assert resp.status_code == 403


class TestReadState:
    def test_mark_read_updates_unread_count(self, client):
        alice = register(client, "alice")
        bob = register(client, "bob")
        chat = open_direct_chat(client, alice, get_me_id(client, bob))
        msg = send_message(client, alice, chat["id"], "hello")

        # Bob sees one unread message.
        resp = client.get("/api/v1/chats/my", headers=auth_headers(bob))
        assert resp.json()[0]["unread_count"] == 1

        # Bob marks the chat as read (message_id omitted -> last message).
        resp = client.post(
            f"/api/v1/chats/{chat['id']}/read",
            headers=auth_headers(bob),
            json={},
        )
        assert resp.status_code == 200
        assert resp.json()["unread_count"] == 0

        # Sender's own messages are never counted as unread.
        resp = client.get("/api/v1/chats/my", headers=auth_headers(alice))
        assert resp.json()[0]["unread_count"] == 0
        assert msg["text"] == "hello"

    def test_mark_read_with_explicit_message_id(self, client):
        alice = register(client, "alice")
        bob = register(client, "bob")
        chat = open_direct_chat(client, alice, get_me_id(client, bob))
        msg = send_message(client, alice, chat["id"], "hi")
        resp = client.post(
            f"/api/v1/chats/{chat['id']}/read",
            headers=auth_headers(bob),
            json={"message_id": msg["id"]},
        )
        assert resp.status_code == 200
        assert resp.json()["unread_count"] == 0

    def test_mark_read_empty_chat_400(self, client):
        alice = register(client, "alice")
        bob = register(client, "bob")
        chat = open_direct_chat(client, alice, get_me_id(client, bob))
        resp = client.post(
            f"/api/v1/chats/{chat['id']}/read",
            headers=auth_headers(bob),
            json={},
        )
        assert resp.status_code == 400

    def test_mark_read_foreign_message_400(self, client):
        alice = register(client, "alice")
        bob = register(client, "bob")
        carol = register(client, "carol")
        chat = open_direct_chat(client, alice, get_me_id(client, bob))
        msg = send_message(client, alice, chat["id"], "hi")
        carol_chat = open_direct_chat(client, alice, get_me_id(client, carol))
        resp = client.post(
            f"/api/v1/chats/{carol_chat['id']}/read",
            headers=auth_headers(carol),
            json={"message_id": msg["id"]},
        )
        assert resp.status_code == 400



class TestGroupAvatar:
    def test_presign_and_confirm(self, client):
        alice = register(client, "alice")
        chat = _create_group(client, alice, "Family", [])
        presign = client.post(
            f"/api/v1/chats/{chat['id']}/avatar/presign",
            headers=auth_headers(alice),
            json={"content_type": "image/png", "size": 1024},
        )
        assert presign.status_code == 200
        avatar_key = presign.json()["avatar_key"]
        assert avatar_key.startswith(f"chats/{chat['id']}/avatar/")

        resp = client.post(
            f"/api/v1/chats/{chat['id']}/avatar/confirm",
            headers=auth_headers(alice),
            json={"avatar_key": avatar_key},
        )
        assert resp.status_code == 200
        assert avatar_key in resp.json()["avatar_url"]

    def test_presign_rejects_non_image(self, client):
        alice = register(client, "alice")
        chat = _create_group(client, alice, "Family", [])
        resp = client.post(
            f"/api/v1/chats/{chat['id']}/avatar/presign",
            headers=auth_headers(alice),
            json={"content_type": "text/html", "size": 1024},
        )
        assert resp.status_code == 422

    def test_confirm_rejects_foreign_prefix(self, client):
        alice = register(client, "alice")
        chat = _create_group(client, alice, "Family", [])
        resp = client.post(
            f"/api/v1/chats/{chat['id']}/avatar/confirm",
            headers=auth_headers(alice),
            json={"avatar_key": "chats/999999/avatar/x.png"},
        )
        assert resp.status_code == 422

    def test_non_member_cannot_presign(self, client):
        alice = register(client, "alice")
        carol = register(client, "carol")
        chat = _create_group(client, alice, "Family", [])
        resp = client.post(
            f"/api/v1/chats/{chat['id']}/avatar/presign",
            headers=auth_headers(carol),
            json={"content_type": "image/png", "size": 1024},
        )
        assert resp.status_code == 404


class TestDeleteChat:
    def test_delete_chat(self, client):
        alice = register(client, "alice")
        bob = register(client, "bob")
        chat = open_direct_chat(client, alice, get_me_id(client, bob))
        resp = client.delete(f"/api/v1/chats/{chat['id']}", headers=auth_headers(alice))
        assert resp.status_code == 204
        resp = client.get(f"/api/v1/chats/{chat['id']}", headers=auth_headers(alice))
        assert resp.status_code == 404

    def test_delete_missing_chat_404(self, client):
        tokens = register(client, "alice")
        resp = client.delete("/api/v1/chats/999999", headers=auth_headers(tokens))
        assert resp.status_code == 404

