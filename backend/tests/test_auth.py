"""Auth endpoint tests: register, login, refresh."""

from __future__ import annotations

from utils import auth_headers, get_me, login, register


class TestRegister:
    def test_register_returns_tokens(self, client):
        tokens = register(client, "alice")
        assert tokens["token_type"] == "bearer"
        assert tokens["access_token"]
        assert tokens["refresh_token"]
        assert tokens["access_token"] != tokens["refresh_token"]

    def test_register_duplicate_username_conflict(self, client):
        register(client, "alice")
        resp = client.post(
            "/api/v1/auth/register",
            json={"username": "alice", "password": "secret123"},
        )
        assert resp.status_code == 409
        assert resp.json()["detail"] == "Username already registered"

    def test_register_short_password_validation_error(self, client):
        resp = client.post(
            "/api/v1/auth/register",
            json={"username": "bob", "password": "12345"},
        )
        assert resp.status_code == 422

    def test_register_makes_user_visible(self, client):
        tokens = register(client, "alice")
        me = get_me(client, tokens)
        assert me["username"] == "alice"


class TestLogin:
    def test_login_success(self, client):
        register(client, "alice")
        tokens = login(client, "alice")
        assert tokens["access_token"]

    def test_login_wrong_password(self, client):
        register(client, "alice")
        resp = client.post(
            "/api/v1/auth/token",
            data={"username": "alice", "password": "wrongpass"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Incorrect username or password"

    def test_login_unknown_user(self, client):
        resp = client.post(
            "/api/v1/auth/token",
            data={"username": "ghost", "password": "secret123"},
        )
        assert resp.status_code == 401


class TestRefresh:
    def test_refresh_success(self, client):
        tokens = register(client, "alice")
        resp = client.post(
            "/api/v1/auth/token/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert resp.status_code == 200
        refreshed = resp.json()
        assert refreshed["access_token"]
        assert refreshed["token_type"] == "bearer"
        # The refreshed access token is usable.
        assert client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {refreshed['access_token']}"},
        ).status_code == 200

    def test_refresh_with_access_token_rejected(self, client):
        tokens = register(client, "alice")
        resp = client.post(
            "/api/v1/auth/token/refresh",
            json={"refresh_token": tokens["access_token"]},
        )
        assert resp.status_code == 401

    def test_refresh_with_garbage_rejected(self, client):
        resp = client.post(
            "/api/v1/auth/token/refresh",
            json={"refresh_token": "not-a-jwt"},
        )
        assert resp.status_code == 401


class TestProtectedRoute:
    def test_no_token_unauthorized(self, client):
        assert client.get("/api/v1/users/me").status_code == 401

    def test_garbage_token_unauthorized(self, client):
        resp = client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer garbage"},
        )
        assert resp.status_code == 401

    def test_refresh_token_as_access_rejected(self, client):
        tokens = register(client, "alice")
        resp = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
        )
        assert resp.status_code == 401

    def test_valid_token_accepted(self, client):
        tokens = register(client, "alice")
        resp = client.get("/api/v1/users/me", headers=auth_headers(tokens))
        assert resp.status_code == 200
