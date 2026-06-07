"""Доступ к БД из контекста приложения + сериализация документов."""

from __future__ import annotations

from typing import Any

from flask import current_app


def get_db():
    """Текущая БД (PyMongo или mongomock в тестах) — кладётся в config фабрикой."""
    return current_app.config["DB"]


def serialize(doc: dict[str, Any] | None) -> dict[str, Any] | None:
    """Документ Mongo → JSON-совместимый dict: `_id` (ObjectId) → строковый `id`."""
    if doc is None:
        return None
    out = dict(doc)
    _id = out.pop("_id", None)
    if _id is not None:
        out["id"] = str(_id)
    return out
