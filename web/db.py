"""Databasåtkomst från applikationskontexten + serialisering av dokument."""

from __future__ import annotations

from typing import Any

from flask import current_app


def get_db():
    """Aktuell databas (PyMongo eller mongomock i tester) — läggs i config av fabriken."""
    return current_app.config["DB"]


def serialize(doc: dict[str, Any] | None) -> dict[str, Any] | None:
    """Mongo-dokument → JSON-kompatibel dict: `_id` (ObjectId) → sträng-`id`."""
    if doc is None:
        return None
    out = dict(doc)
    _id = out.pop("_id", None)
    if _id is not None:
        out["id"] = str(_id)
    return out
