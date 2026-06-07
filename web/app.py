"""Фабрика Flask-приложения.

Запуск (dev):  flask --app web.app run --debug
Health-check:  GET /health  (BE-API-008)

Blueprints (auth/api/sse) подключаются по мере реализации (Фазы 4, 6).
"""

from __future__ import annotations

from flask import Flask, jsonify
from shared.config import get_settings


def create_app() -> Flask:
    settings = get_settings()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key

    @app.get("/health")
    def health():
        return jsonify(status="ok", service="hqrtm-web")

    # TODO(Фаза 4): app.register_blueprint(auth_bp), api_bp
    # TODO(Фаза 6): app.register_blueprint(sse_bp)  # /sse/feed

    return app


app = create_app()
