"""Blueprint веб-страниц (Jinja2 + Tailwind + Vanilla JS) — Фаза 5.

Страницы отдают HTML-каркас; данные подгружает клиентский JS через REST API
(токены в localStorage, защита маршрутов на клиенте — FE-AU-003).
Боевой фронтенд по канону: Flask + Jinja2 + Tailwind + Vanilla JS (без React).
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
    # Серверной гард-проверки нет (фронтенд-гард + admin-API 403); страница только для admin.
    return render_template("admin.html", page="admin")
