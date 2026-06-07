"""Тесты веб-страниц (Jinja2 + Tailwind) — Фаза 5."""

from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    "path,marker",
    [
        ("/", b"Real-Time Monitor"),
        ("/login", b"Logga in"),
        ("/register", b"Skapa konto"),
        ("/app", b"Fl\xc3\xb6de"),  # «Flöde» в UTF-8
        ("/app/filters", b"Filter"),
        ("/app/notifications", b"Aviseringar"),
        ("/app/settings", b"GDPR"),
    ],
)
def test_pages_render(client, path, marker):
    resp = client.get(path)
    assert resp.status_code == 200
    assert marker in resp.data


def test_pages_load_api_client(client):
    # на каждой странице подключён клиент API
    assert b"js/api.js" in client.get("/").data
    assert b"js/api.js" in client.get("/app").data


def test_me_returns_role(client, make_user, bearer):
    h = bearer(make_user()["access_token"])
    data = client.get("/api/me", headers=h).get_json()
    assert data["role"] == "user"
