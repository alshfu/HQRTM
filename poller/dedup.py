"""Дедупликация объявлений через seen_listings (BE-FL-003).

Ключ — (source, external_id) с unique-индексом. Первая встреча → запись и True;
повторная → DuplicateKeyError → False. TTL-индекс на seen_at авто-чистит старое (без Redis).
"""

from __future__ import annotations

from datetime import UTC, datetime

from pymongo.errors import DuplicateKeyError
from shared.db import COLL_SEEN


def mark_seen(db, source: str, external_id: str) -> bool:
    """Отметить объявление виденным. Возвращает True, если оно новое (впервые)."""
    try:
        db[COLL_SEEN].insert_one(
            {"source": source, "external_id": external_id, "seen_at": datetime.now(UTC)}
        )
        return True
    except DuplicateKeyError:
        return False
