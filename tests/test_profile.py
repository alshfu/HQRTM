"""Tester för ansökningsprofilen (/api/profile) — auth, validering, isolering."""

from __future__ import annotations


def test_profile_empty_then_put_and_get(client, make_user, bearer):
    u = make_user()
    h = bearer(u["access_token"])

    assert client.get("/api/profile", headers=h).get_json() == {}

    resp = client.put(
        "/api/profile",
        headers=h,
        json={
            "presentation": "Hej, jag är skötsam.",
            "income": "35000",
            "occupation": "Utvecklare",
            "junk": "ignoreras",
        },
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["presentation"] == "Hej, jag är skötsam."
    assert data["income"] == 35000  # sträng → heltal
    assert data["occupation"] == "Utvecklare"
    assert "junk" not in data  # okända fält ignoreras

    assert client.get("/api/profile", headers=h).get_json()["income"] == 35000


def test_profile_requires_auth(client):
    assert client.get("/api/profile").status_code == 401
    assert client.put("/api/profile", json={}).status_code == 401


def test_profile_isolated_per_user(client, make_user, bearer):
    a = make_user("a@x.se")
    b = make_user("b@x.se")
    client.put("/api/profile", headers=bearer(a["access_token"]), json={"phone": "0700000000"})

    assert client.get("/api/profile", headers=bearer(b["access_token"])).get_json() == {}
