"""Tester för observerbarhet/säkerhet (Fas 8): PII-maskering, säkerhetsheaders, readiness."""

from __future__ import annotations

from shared.logging import redact_pii


def test_redact_email():
    assert redact_pii("login from elin@hqrtm.se ok") == "login from [email] ok"


def test_redact_bearer_token():
    out = redact_pii("Authorization: Bearer abc.def-123_XYZ")
    assert "abc.def" not in out
    assert "Bearer [redacted]" in out


def test_redact_long_number_chat_id():
    assert redact_pii("telegram chat_id=123456789 levererad") == "telegram chat_id=[id] levererad"


def test_short_numbers_kept():
    # Korta tal (latens, status) ska inte maskeras.
    assert redact_pii("latency_ms=420 status=200") == "latency_ms=420 status=200"


def test_security_headers_present(client):
    resp = client.get("/health")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["Referrer-Policy"] == "no-referrer"
    assert "frame-ancestors" in resp.headers["Content-Security-Policy"]


def test_hsts_absent_in_testing(client):
    # HSTS sätts inte i testläge (app.testing=True).
    resp = client.get("/health")
    assert "Strict-Transport-Security" not in resp.headers


def test_health_liveness(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_health_ready_pings_db(client):
    # mongomock svarar på ping → readiness ok.
    resp = client.get("/health/ready")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "ready"
    assert body["db"] == "ok"
