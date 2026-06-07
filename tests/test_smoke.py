"""Smoke-тесты Фазы 0: приложение собирается, health отвечает, модули импортируются."""

from __future__ import annotations

from web.app import create_app


def test_health_ok():
    app = create_app()
    client = app.test_client()
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_packages_importable():
    import bot.main  # noqa: F401
    import poller.main  # noqa: F401
    import shared.config  # noqa: F401
    import shared.db  # noqa: F401
