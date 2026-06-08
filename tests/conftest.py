"""Gemensamma fixturer för webbtester (Flask + mongomock)."""

from __future__ import annotations

import mongomock
import pytest
from shared.db import ensure_indexes
from web.app import create_app


@pytest.fixture
def db():
    database = mongomock.MongoClient()["hqrtm_test"]
    ensure_indexes(database)
    return database


@pytest.fixture
def client(db):
    return create_app(db=db, testing=True).test_client()


@pytest.fixture
def make_user(client):
    """Användarfabrik: registrerar och returnerar JSON med id och token."""

    def _make(email: str = "elin@hqrtm.se", password: str = "demo1234") -> dict:
        resp = client.post("/auth/register", json={"email": email, "password": password})
        assert resp.status_code == 201, resp.get_json()
        return resp.get_json()

    return _make


@pytest.fixture
def bearer():
    """Hjälpfunktion för auktoriseringsrubrik."""

    def _bearer(token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}

    return _bearer
