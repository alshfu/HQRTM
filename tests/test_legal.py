"""Tester för de offentliga juridiska sidorna (integritetspolicy + villkor)."""

from __future__ import annotations


def test_privacy_page(client):
    resp = client.get("/privacy")
    assert resp.status_code == 200
    assert "Integritetspolicy" in resp.get_data(as_text=True)


def test_terms_page(client):
    resp = client.get("/terms")
    assert resp.status_code == 200
    assert "Användarvillkor" in resp.get_data(as_text=True)
