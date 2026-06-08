"""Tester av admin-API (rollen admin): åtkomstskydd, statistik, hantering av roller."""

from __future__ import annotations

from bson import ObjectId
from shared.db import COLL_USERS
from shared.models import UserRole


def _make_admin(db, make_user, email="admin@hqrtm.se"):
    """Registrera en användare och höj till admin (rollen läses från DB)."""
    u = make_user(email=email, password="admin1234")
    db[COLL_USERS].update_one({"_id": ObjectId(u["id"])}, {"$set": {"role": UserRole.ADMIN.value}})
    return u


def test_stats_requires_auth(client):
    assert client.get("/api/admin/stats").status_code == 401


def test_stats_forbidden_for_regular_user(client, make_user, bearer):
    u = make_user()
    resp = client.get("/api/admin/stats", headers=bearer(u["access_token"]))
    assert resp.status_code == 403


def test_stats_ok_for_admin(client, db, make_user, bearer):
    admin = _make_admin(db, make_user)
    resp = client.get("/api/admin/stats", headers=bearer(admin["access_token"]))
    assert resp.status_code == 200
    data = resp.get_json()
    assert set(data) == {"users", "filters", "listings", "notifications"}
    assert data["users"] >= 1


def test_users_list_for_admin(client, db, make_user, bearer):
    admin = _make_admin(db, make_user)
    make_user(email="elin@hqrtm.se")  # vanlig användare
    resp = client.get("/api/admin/users", headers=bearer(admin["access_token"]))
    assert resp.status_code == 200
    data = resp.get_json()
    emails = {u["email"] for u in data["items"]}
    assert {"admin@hqrtm.se", "elin@hqrtm.se"} <= emails
    # hemligheter läcker inte
    assert all("password_hash" not in u for u in data["items"])


def test_users_list_forbidden_for_regular(client, make_user, bearer):
    u = make_user()
    assert client.get("/api/admin/users", headers=bearer(u["access_token"])).status_code == 403


def test_promote_user_to_admin(client, db, make_user, bearer):
    admin = _make_admin(db, make_user)
    target = make_user(email="elin@hqrtm.se")
    resp = client.post(
        f"/api/admin/users/{target['id']}/role",
        json={"role": "admin"},
        headers=bearer(admin["access_token"]),
    )
    assert resp.status_code == 200
    doc = db[COLL_USERS].find_one({"_id": ObjectId(target["id"])})
    assert doc["role"] == UserRole.ADMIN.value


def test_cannot_demote_self(client, db, make_user, bearer):
    admin = _make_admin(db, make_user)
    resp = client.post(
        f"/api/admin/users/{admin['id']}/role",
        json={"role": "user"},
        headers=bearer(admin["access_token"]),
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "cannot_demote_self"
    # rollen ändrades inte
    doc = db[COLL_USERS].find_one({"_id": ObjectId(admin["id"])})
    assert doc["role"] == UserRole.ADMIN.value


def test_bad_role_rejected(client, db, make_user, bearer):
    admin = _make_admin(db, make_user)
    target = make_user(email="elin@hqrtm.se")
    resp = client.post(
        f"/api/admin/users/{target['id']}/role",
        json={"role": "superuser"},
        headers=bearer(admin["access_token"]),
    )
    assert resp.status_code == 400


def test_set_role_unknown_user(client, db, make_user, bearer):
    admin = _make_admin(db, make_user)
    resp = client.post(
        f"/api/admin/users/{ObjectId()}/role",
        json={"role": "admin"},
        headers=bearer(admin["access_token"]),
    )
    assert resp.status_code == 404


def test_admin_page_renders(client):
    """Sidan /app/admin levereras (klientskyddet — internt)."""
    resp = client.get("/app/admin")
    assert resp.status_code == 200
    assert b"admin" in resp.data.lower()
