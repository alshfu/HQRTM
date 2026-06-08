"""Dedup av annonser via seen_listings (BE-FL-003).

Nyckel — (source, external_id) med unique-index. Första gången → post och True;
upprepad → DuplicateKeyError → False. TTL-index på seen_at auto-rensar gammalt (utan Redis).
"""

from __future__ import annotations

from datetime import UTC, datetime

from pymongo.errors import DuplicateKeyError
from shared.db import COLL_SEEN


def mark_seen(db, source: str, external_id: str) -> bool:
    """Markera annonsen som sedd. Returnerar True om den är ny (första gången)."""
    try:
        db[COLL_SEEN].insert_one(
            {"source": source, "external_id": external_id, "seen_at": datetime.now(UTC)}
        )
        return True
    except DuplicateKeyError:
        return False
