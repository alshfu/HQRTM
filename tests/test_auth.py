"""Tester av autentisering (register/login/refresh)."""

from __future__ import annotations


def test_register_returns_tokens(make_user):
    data = make_user()
    assert "access_token" in data and "refresh_token" in data
    assert data["id"]


def test_register_duplicate_email(client, make_user):
    make_user()
    resp = client.post("/auth/register", json={"email": "elin@hqrtm.se", "password": "demo1234"})
    assert resp.status_code == 409


def test_register_weak_password(client):
    resp = client.post("/auth/register", json={"email": "a@b.se", "password": "short"})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "weak_password"


def test_register_invalid_email(client):
    resp = client.post("/auth/register", json={"email": "not-email", "password": "demo1234"})
    assert resp.status_code == 400


def test_login_ok_and_wrong_password(client, make_user):
    make_user()
    ok = client.post("/auth/login", json={"email": "elin@hqrtm.se", "password": "demo1234"})
    assert ok.status_code == 200 and "access_token" in ok.get_json()

    bad = client.post("/auth/login", json={"email": "elin@hqrtm.se", "password": "WRONGpass"})
    assert bad.status_code == 401


def test_refresh_flow(client, make_user):
    data = make_user()
    resp = client.post("/auth/refresh", json={"refresh_token": data["refresh_token"]})
    assert resp.status_code == 200 and "access_token" in resp.get_json()


def test_refresh_rejects_access_token(client, make_user):
    data = make_user()
    # skickar access i stället för refresh — ska avvisas (kontroll av type)
    resp = client.post("/auth/refresh", json={"refresh_token": data["access_token"]})
    assert resp.status_code == 401
