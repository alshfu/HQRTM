"""Blueprint för webbsidor (Jinja2 + Tailwind + Vanilla JS) — Fas 5.

Sidorna levererar HTML-stomme; data hämtas av klient-JS via REST API
(tokens i localStorage, skydd av rutter på klienten — FE-AU-003).
Produktionsfrontend enligt kanon: Flask + Jinja2 + Tailwind + Vanilla JS (utan React).
"""

from __future__ import annotations

from flask import Blueprint, render_template

bp = Blueprint("views", __name__)


@bp.get("/")
def index():
    return render_template("index.html")


@bp.get("/login")
def login():
    return render_template("login.html")


@bp.get("/privacy")
def privacy():
    return render_template("privacy.html")


@bp.get("/terms")
def terms():
    return render_template("terms.html")


@bp.get("/register")
def register():
    return render_template("register.html")


@bp.get("/app")
def dashboard():
    return render_template("dashboard.html", page="feed")


@bp.get("/app/filters")
def filters():
    return render_template("filters.html", page="filters")


@bp.get("/app/notifications")
def notifications():
    return render_template("notifications.html", page="notifications")


@bp.get("/app/settings")
def settings():
    return render_template("settings.html", page="settings")


@bp.get("/app/admin")
def admin():
    # Inget server-skydd här (frontend-skydd + admin-API 403); sidan är bara för admin.
    return render_template("admin.html", page="admin")
