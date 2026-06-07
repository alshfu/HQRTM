"""Тесты эндпоинтов Фазы 4: listings, notifications, telegram, OpenAPI."""

from __future__ import annotations

from shared.db import COLL_LISTINGS, COLL_NOTIFICATIONS


def test_listings_pagination_and_filter(client, make_user, bearer, db):
    h = bearer(make_user()["access_token"])
    db[COLL_LISTINGS].insert_many(
        [
            {
                "source": "homeq",
                "external_id": f"h{i}",
                "title": f"t{i}",
                "url": "u",
                "district": "Söder",
                "listing_type": "fcfs",
            }
            for i in range(25)
        ]
    )
    # первая страница (дефолт limit=20)
    r1 = client.get("/api/listings", headers=h).get_json()
    assert r1["total"] == 25 and len(r1["items"]) == 20 and r1["page"] == 1
    # вторая страница
    r2 = client.get("/api/listings?page=2", headers=h).get_json()
    assert len(r2["items"]) == 5
    # фильтр по source (нет qasa)
    rq = client.get("/api/listings?source=qasa", headers=h).get_json()
    assert rq["total"] == 0


def test_listings_matched(client, make_user, bearer, db):
    data = make_user()
    h = bearer(data["access_token"])
    res = db[COLL_LISTINGS].insert_one(
        {"source": "homeq", "external_id": "m1", "title": "match", "url": "u"}
    )
    db[COLL_NOTIFICATIONS].insert_one(
        {"user_id": data["id"], "listing_id": str(res.inserted_id), "status": "delivered"}
    )
    matched = client.get("/api/listings?matched=true", headers=h).get_json()
    assert matched["total"] == 1 and matched["items"][0]["external_id"] == "m1"


def test_notifications_history(client, make_user, bearer, db):
    data = make_user()
    h = bearer(data["access_token"])
    db[COLL_NOTIFICATIONS].insert_many(
        [{"user_id": data["id"], "listing_id": f"l{i}", "status": "delivered"} for i in range(3)]
    )
    # уведомление другого пользователя не должно попасть
    db[COLL_NOTIFICATIONS].insert_one({"user_id": "someone_else", "listing_id": "x"})
    resp = client.get("/api/notifications", headers=h).get_json()
    assert resp["total"] == 3


def test_telegram_link_and_status(client, make_user, bearer):
    h = bearer(make_user()["access_token"])
    link = client.post("/api/telegram/link", headers=h)
    assert link.status_code == 200
    assert link.get_json()["link_code"]

    status = client.get("/api/telegram/status", headers=h)
    assert status.status_code == 200
    assert status.get_json()["linked"] is False


def test_openapi_spec_and_docs(client):
    spec = client.get("/openapi.json")
    assert spec.status_code == 200
    body = spec.get_json()
    assert body["openapi"].startswith("3.")
    assert "/api/filters" in body["paths"]
    assert "/api/listings" in body["paths"]

    docs = client.get("/apidocs")
    assert docs.status_code == 200
    assert b"swagger-ui" in docs.data
