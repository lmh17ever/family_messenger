"""HTTP helpers shared by integration tests."""

from __future__ import annotations


def register(client, username: str, password: str = "secret123") -> dict:
    """Register a new user and return the token payload."""
    resp = client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def login(client, username: str, password: str = "secret123") -> dict:
    resp = client.post(
        "/api/v1/auth/token",
        data={"username": username, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def auth_headers(tokens: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def get_me(client, tokens: dict) -> dict:
    resp = client.get("/api/v1/users/me", headers=auth_headers(tokens))
    assert resp.status_code == 200, resp.text
    return resp.json()


def get_me_id(client, tokens: dict) -> int:
    return get_me(client, tokens)["id"]


def open_direct_chat(client, tokens: dict, other_user_id: int) -> dict:
    """Open (or fetch) a direct chat with ``other_user_id``."""
    resp = client.post(f"/api/v1/chats/{other_user_id}", headers=auth_headers(tokens))
    assert resp.status_code == 200, resp.text
    return resp.json()


def send_message(client, tokens: dict, chat_id: int, text: str, **extra) -> dict:
    resp = client.post(
        f"/api/v1/chats/{chat_id}/messages",
        headers=auth_headers(tokens),
        json={"text": text, **extra},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()
