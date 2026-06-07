"""Тесты SSE: брокер, авторизация эндпоинта, доставка события, очистка подписки."""

from __future__ import annotations

from web.sse.broker import Broker, broker


def test_broker_pubsub():
    b = Broker()
    q = b.subscribe("u1")
    assert b.publish("u1", {"x": 1}) == 1
    assert q.get_nowait() == {"x": 1}
    # другому пользователю не доставляется
    assert b.publish("u2", {"y": 2}) == 0
    b.unsubscribe("u1", q)
    assert b.subscriber_count("u1") == 0


def test_sse_requires_token(client):
    assert client.get("/sse/feed").status_code == 401


def test_sse_streams_event_and_cleans_up(client, make_user):
    data = make_user()
    uid = data["id"]
    token = data["access_token"]

    resp = client.get(f"/sse/feed?token={token}")
    assert resp.status_code == 200
    assert resp.mimetype == "text/event-stream"

    # клиент подписан → публикуем совпадение
    assert broker.subscriber_count(uid) == 1
    broker.publish(uid, {"type": "match", "listing": {"external_id": "x1"}})

    body = resp.get_data(as_text=True)
    assert ": connected" in body
    assert "data:" in body
    assert "x1" in body

    # после завершения стрима подписка снята (разрыв соединения)
    assert broker.subscriber_count(uid) == 0
