"""Fabrik för Flask-applikationen.

Körning (dev):  flask --app web.app run --debug
Health-check:   GET /health  (BE-API-008)

Blueprints: auth (/auth), api (/api). SSE (/sse/feed) — Fas 6.
"""

from __future__ import annotations

from flask import Flask, jsonify
from shared.config import get_settings


def create_app(db=None, testing: bool = False) -> Flask:
    """Skapa applikationen.

    db: databasobjekt (PyMongo eller mongomock). Om None — riktig databas från inställningar.
    testing: i tester stänger av rate-limiting och sätter app.testing.
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

    from web.i18n import init_i18n

    init_i18n(app)

    from web.admin.routes import bp as admin_bp
    from web.api.routes import bp as api_bp
    from web.auth.routes import bp as auth_bp
    from web.sse.routes import bp as sse_bp
    from web.views import bp as views_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(sse_bp)
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

    return app


# Ingångspunkt för `flask --app web.app run`. Databasen ansluts lat (PyMongo ansluter inte
# före första begäran), därför är importen säker även i tester.
app = create_app()
