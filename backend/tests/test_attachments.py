"""Attachment endpoint tests: presign, confirm, download URL, linking."""

from __future__ import annotations

from utils import auth_headers, get_me_id, open_direct_chat, register, send_message


def _setup(client):
    alice = register(client, "alice")
    bob = register(client, "bob")
    chat = open_direct_chat(client, alice, get_me_id(client, bob))
    return alice, bob, chat


def _presign(client, tokens, chat_id, **overrides):
    payload = {
        "filename": "doc.png",
        "content_type": "image/png",
        "size": 1024,
        **overrides,
    }
    return client.post(
        f"/api/v1/chats/{chat_id}/attachments/presign",
        headers=auth_headers(tokens),
        json=payload,
    )


class TestPresign:
    def test_presign_success(self, client):
        alice, _bob, chat = _setup(client)
        resp = _presign(client, alice, chat["id"])
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["attachment_id"] > 0
        assert body["upload"]["url"]

    def test_presign_rejects_dangerous_content_type(self, client):
        alice, _bob, chat = _setup(client)
        resp = _presign(
            client, alice, chat["id"], content_type="text/html", filename="x.html"
        )
        assert resp.status_code == 422

    def test_presign_rejects_oversize(self, client):
        alice, _bob, chat = _setup(client)
        # MAX_ATTACHMENT_SIZE is 500 MB (converted to bytes by Settings).
        resp = _presign(
            client, alice, chat["id"], size=501 * 1024 * 1024
        )
        assert resp.status_code == 422

    def test_presign_requires_membership(self, client):
        alice, _bob, chat = _setup(client)
        carol = register(client, "carol")
        resp = _presign(client, carol, chat["id"])
        assert resp.status_code == 404


class TestConfirm:
    def test_confirm_success(self, client):
        alice, _bob, chat = _setup(client)
        attachment_id = _presign(client, alice, chat["id"]).json()["attachment_id"]
        resp = client.post(
            f"/api/v1/attachments/{attachment_id}/confirm",
            headers=auth_headers(alice),
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["id"] == attachment_id
        # Metadata comes from head_object (mocked S3).
        assert body["size"] == 1024
        assert body["content_type"] == "image/png"
        assert body["url"]

    def test_confirm_missing_object_400(self, client, s3_mock):
        alice, _bob, chat = _setup(client)
        attachment_id = _presign(client, alice, chat["id"]).json()["attachment_id"]
        s3_mock.head_object.return_value = None
        resp = client.post(
            f"/api/v1/attachments/{attachment_id}/confirm",
            headers=auth_headers(alice),
        )
        assert resp.status_code == 400

    def test_confirm_not_uploader_404(self, client):
        alice, bob, chat = _setup(client)
        attachment_id = _presign(client, alice, chat["id"]).json()["attachment_id"]
        resp = client.post(
            f"/api/v1/attachments/{attachment_id}/confirm",
            headers=auth_headers(bob),
        )
        assert resp.status_code == 404

    def test_confirm_missing_attachment_404(self, client):
        alice, _bob, _chat = _setup(client)
        resp = client.post(
            "/api/v1/attachments/999999/confirm", headers=auth_headers(alice)
        )
        assert resp.status_code == 404


class TestDownloadUrl:
    def test_member_gets_url(self, client):
        alice, _bob, chat = _setup(client)
        attachment_id = _presign(client, alice, chat["id"]).json()["attachment_id"]
        resp = client.get(
            f"/api/v1/attachments/{attachment_id}/url", headers=auth_headers(alice)
        )
        assert resp.status_code == 200
        assert resp.json()["url"]

    def test_non_member_404(self, client):
        alice, _bob, chat = _setup(client)
        attachment_id = _presign(client, alice, chat["id"]).json()["attachment_id"]
        carol = register(client, "carol")
        resp = client.get(
            f"/api/v1/attachments/{attachment_id}/url", headers=auth_headers(carol)
        )
        assert resp.status_code == 404

    def test_missing_attachment_404(self, client):
        alice, _bob, _chat = _setup(client)
        resp = client.get(
            "/api/v1/attachments/999999/url", headers=auth_headers(alice)
        )
        assert resp.status_code == 404



class TestAttachToMessage:
    def test_message_with_attachment(self, client):
        alice, _bob, chat = _setup(client)
        attachment_id = _presign(client, alice, chat["id"]).json()["attachment_id"]
        resp = client.post(
            f"/api/v1/chats/{chat['id']}/messages",
            headers=auth_headers(alice),
            json={"attachment_ids": [attachment_id]},
        )
        assert resp.status_code == 200, resp.text
        attachments = resp.json()["attachments"]
        assert len(attachments) == 1
        assert attachments[0]["id"] == attachment_id
        assert attachments[0]["url"]

    def test_unknown_attachment_422(self, client):
        alice, _bob, chat = _setup(client)
        resp = client.post(
            f"/api/v1/chats/{chat['id']}/messages",
            headers=auth_headers(alice),
            json={"attachment_ids": [999999]},
        )
        assert resp.status_code == 422

    def test_foreign_attachment_403(self, client):
        alice, bob, chat = _setup(client)
        # Bob uploads an attachment...
        bob_attachment = _presign(client, bob, chat["id"]).json()["attachment_id"]
        # ...Alice may not attach it to her message.
        resp = client.post(
            f"/api/v1/chats/{chat['id']}/messages",
            headers=auth_headers(alice),
            json={"attachment_ids": [bob_attachment]},
        )
        assert resp.status_code == 403

    def test_reused_attachment_422(self, client):
        alice, _bob, chat = _setup(client)
        attachment_id = _presign(client, alice, chat["id"]).json()["attachment_id"]
        first = client.post(
            f"/api/v1/chats/{chat['id']}/messages",
            headers=auth_headers(alice),
            json={"attachment_ids": [attachment_id]},
        )
        assert first.status_code == 200
        second = client.post(
            f"/api/v1/chats/{chat['id']}/messages",
            headers=auth_headers(alice),
            json={"attachment_ids": [attachment_id]},
        )
        assert second.status_code == 422

    def test_duplicate_ids_rejected(self, client):
        alice, _bob, chat = _setup(client)
        attachment_id = _presign(client, alice, chat["id"]).json()["attachment_id"]
        resp = client.post(
            f"/api/v1/chats/{chat['id']}/messages",
            headers=auth_headers(alice),
            json={"attachment_ids": [attachment_id, attachment_id]},
        )
        assert resp.status_code == 422

    def test_message_text_and_attachment_combined(self, client):
        alice, _bob, chat = _setup(client)
        attachment_id = _presign(client, alice, chat["id"]).json()["attachment_id"]
        resp = client.post(
            f"/api/v1/chats/{chat['id']}/messages",
            headers=auth_headers(alice),
            json={"text": "see attached", "attachment_ids": [attachment_id]},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["text"] == "see attached"
        assert len(body["attachments"]) == 1

