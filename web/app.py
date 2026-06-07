"""Фабрика Flask-приложения.

Запуск (dev):  flask --app web.app run --debug
Health-check:  GET /health  (BE-API-008)

Blueprints: auth (/auth), api (/api). SSE (/sse/feed) — Фаза 6.
"""

from __future__ import annotations

from flask import Flask, jsonify
from shared.config import get_settings


def create_app(db=None, testing: bool = False) -> Flask:
    """Создать приложение.

    db: объект БД (PyMongo или mongomock). Если None — реальная БД из настроек.
    testing: в тестах отключает rate-limiting и помечает app.testing.
    """
    settings = get_settings()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key
    app.testing = testing
    app.config["RATELIMIT_ENABLED"] = not testing

    if db is None:
        from shared.db import get_sync_db

        db = get_sync_db()
    app.config["DB"] = db

    from web.extensions import limiter

    limiter.init_app(app)

    from web.api.routes import bp as api_bp
    from web.auth.routes import bp as auth_bp
    from web.views import bp as views_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(views_bp)

    @app.get("/health")
    def health():
        return jsonify(status="ok", service="hqrtm-web")

    # OpenAPI / Swagger UI (BE-API-009)
    from web.openapi import OPENAPI_SPEC, SWAGGER_UI_HTML

    @app.get("/openapi.json")
    def openapi_spec():
        return jsonify(OPENAPI_SPEC)

    @app.get("/apidocs")
    def apidocs():
        return SWAGGER_UI_HTML

    # TODO(Фаза 6): app.register_blueprint(sse_bp)  # /sse/feed

    return app


# Точка входа для `flask --app web.app run`. БД подключается лениво (PyMongo не коннектится
# до первого запроса), поэтому импорт безопасен и в тестах.
app = create_app()
