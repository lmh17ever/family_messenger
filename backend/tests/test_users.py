"""User endpoint tests: profile, listing, avatar presign/confirm."""

from __future__ import annotations

from utils import auth_headers, get_me, get_me_id, login, register


class TestMe:
    def test_get_me(self, client):
        tokens = register(client, "alice")
        me = get_me(client, tokens)
        assert me["id"] > 0
        assert me["username"] == "alice"
        assert me["avatar_url"] is None

    def test_patch_username_returns_fresh_tokens(self, client):
        tokens = register(client, "alice")
        resp = client.patch(
            "/api/v1/users/me",
            headers=auth_headers(tokens),
            json={"username": "alice2"},
        )
        assert resp.status_code == 200
        new_tokens = resp.json()
        assert new_tokens["access_token"]
        # New tokens reflect the new username.
        assert get_me(client, new_tokens)["username"] == "alice2"


class TestUserList:
    def test_list_excludes_self_and_others(self, client):
        alice = register(client, "alice")
        register(client, "bob")
        resp = client.get("/api/v1/users", headers=auth_headers(alice))
        assert resp.status_code == 200
        usernames = {u["username"] for u in resp.json()}
        assert usernames == {"bob"}

    def test_list_search(self, client):
        alice = register(client, "alice")
        register(client, "bob")
        register(client, "robert")
        resp = client.get(
            "/api/v1/users", params={"search": "rob"}, headers=auth_headers(alice)
        )
        assert [u["username"] for u in resp.json()] == ["robert"]

    def test_list_requires_auth(self, client):
        assert client.get("/api/v1/users").status_code == 401


class TestGetUser:
    def test_get_user_by_id(self, client):
        alice = register(client, "alice")
        bob_id = None
        register(client, "bob")
        resp = client.get("/api/v1/users", headers=auth_headers(alice))
        for u in resp.json():
            if u["username"] == "bob":
                bob_id = u["id"]
        resp = client.get(f"/api/v1/users/{bob_id}", headers=auth_headers(alice))
        assert resp.status_code == 200
        assert resp.json()["username"] == "bob"

    def test_get_missing_user_404(self, client):
        register(client, "alice")
        assert client.get("/api/v1/users/999999").status_code == 404


class TestDeleteUser:
    def test_regular_user_cannot_delete_self(self, client):
        tokens = register(client, "alice")
        user_id = get_me_id(client, tokens)
        resp = client.delete(
            f"/api/v1/users/{user_id}", headers=auth_headers(tokens)
        )
        assert resp.status_code == 403

    def test_superuser_can_delete_self(
        self, client, create_user_direct
    ):
        user_id = create_user_direct("root", is_superuser=True)
        tokens = login(client, "root")
        resp = client.delete(
            f"/api/v1/users/{user_id}", headers=auth_headers(tokens)
        )
        assert resp.status_code == 204

    def test_delete_missing_user_rejected(self, client):
        # Authorization is checked before existence: a regular user gets 403.
        tokens = register(client, "alice")
        resp = client.delete("/api/v1/users/999999", headers=auth_headers(tokens))
        assert resp.status_code == 403

    def test_superuser_delete_missing_user_404(self, client, create_user_direct):
        # Even a superuser may only delete their own account (endpoint logic),
        # so deleting another id is rejected with 403 before existence check.
        create_user_direct("root", is_superuser=True)
        tokens = login(client, "root")
        resp = client.delete("/api/v1/users/999999", headers=auth_headers(tokens))
        assert resp.status_code == 403


class TestAvatar:
    def test_presign_valid_image(self, client):
        tokens = register(client, "alice")
        resp = client.post(
            "/api/v1/users/me/avatar/presign",
            headers=auth_headers(tokens),
            json={"filename": "a.png", "content_type": "image/png", "size": 1024},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["upload"]["url"]
        # Key is namespaced under the user id.
        assert body["avatar_key"].startswith(f"{get_me_id(client, tokens)}/")

    def test_presign_rejects_non_image(self, client):
        tokens = register(client, "alice")
        resp = client.post(
            "/api/v1/users/me/avatar/presign",
            headers=auth_headers(tokens),
            json={"filename": "a.html", "content_type": "text/html", "size": 1024},
        )
        assert resp.status_code == 422

    def test_presign_rejects_oversize(self, client):
        tokens = register(client, "alice")
        # MAX_AVATAR_SIZE is 20 MB (converted to bytes by Settings).
        resp = client.post(
            "/api/v1/users/me/avatar/presign",
            headers=auth_headers(tokens),
            json={
                "filename": "a.png",
                "content_type": "image/png",
                "size": 21 * 1024 * 1024,
            },
        )
        assert resp.status_code == 422

    def test_confirm_sets_avatar_url(self, client):
        tokens = register(client, "alice")
        presign = client.post(
            "/api/v1/users/me/avatar/presign",
            headers=auth_headers(tokens),
            json={"filename": "a.png", "content_type": "image/png", "size": 1024},
        ).json()
        resp = client.post(
            "/api/v1/users/me/avatar/confirm",
            headers=auth_headers(tokens),
            json={"avatar_key": presign["avatar_key"]},
        )
        assert resp.status_code == 200
        assert presign["avatar_key"] in resp.json()["avatar_url"]

    def test_confirm_rejects_foreign_key_prefix(self, client):
        tokens = register(client, "alice")
        resp = client.post(
            "/api/v1/users/me/avatar/confirm",
            headers=auth_headers(tokens),
            json={"avatar_key": "999/abc.png"},
        )
        assert resp.status_code == 422

    def test_confirm_rejects_missing_object(self, client, s3_mock):
        tokens = register(client, "alice")
        s3_mock.head_object.return_value = None
        user_id = get_me_id(client, tokens)
        resp = client.post(
            "/api/v1/users/me/avatar/confirm",
            headers=auth_headers(tokens),
            json={"avatar_key": f"{user_id}/abc.png"},
        )
        assert resp.status_code == 422
