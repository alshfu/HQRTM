"""Тесты API: CRUD фильтров и /me (включая GDPR-удаление)."""

from __future__ import annotations


def test_filters_requires_auth(client):
    assert client.get("/api/filters").status_code == 401


def test_filters_crud(client, make_user, bearer):
    h = bearer(make_user()["access_token"])

    # пусто
    assert client.get("/api/filters", headers=h).get_json()["items"] == []

    # создать
    created = client.post("/api/filters", json={"name": "Söder", "rent_max": 15000}, headers=h)
    assert created.status_code == 201
    fid = created.get_json()["id"]

    # в списке, с дефолтом only_fcfs
    items = client.get("/api/filters", headers=h).get_json()["items"]
    assert len(items) == 1 and items[0]["name"] == "Söder"
    assert items[0]["only_fcfs"] is True

    # обновить
    upd = client.put(f"/api/filters/{fid}", json={"name": "Söder 2", "is_active": False}, headers=h)
    assert upd.status_code == 200

    # удалить
    assert client.delete(f"/api/filters/{fid}", headers=h).status_code == 200
    assert client.get("/api/filters", headers=h).get_json()["items"] == []


def test_update_nonexistent_filter(client, make_user, bearer):
    h = bearer(make_user()["access_token"])
    resp = client.put("/api/filters/0123456789abcdef01234567", json={"name": "x"}, headers=h)
    assert resp.status_code == 404


def test_filters_isolated_between_users(client, make_user, bearer):
    h1 = bearer(make_user()["access_token"])
    client.post("/api/filters", json={"name": "u1"}, headers=h1)

    h2 = bearer(make_user(email="other@hqrtm.se")["access_token"])
    assert client.get("/api/filters", headers=h2).get_json()["items"] == []


def test_me_and_gdpr_delete(client, make_user, bearer):
    h = bearer(make_user()["access_token"])

    me = client.get("/api/me", headers=h)
    assert me.status_code == 200
    assert me.get_json()["email"] == "elin@hqrtm.se"
    assert me.get_json()["telegram_linked"] is False

    # GDPR: удаление аккаунта
    assert client.delete("/api/me", headers=h).status_code == 200
    # пользователя больше нет
    assert client.get("/api/me", headers=h).status_code == 404
