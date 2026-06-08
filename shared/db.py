"""Anslutning till MongoDB och skapande av index (Fas 1).

Två klienter:
- PyMongo (synkron) — för Flask (web).
- Motor (asynkron) — för poller och bot.

Indexen implementerar invarianter i datamodellen (Roadmap §3, utökat för multi-källa):
- DB-001: unikhet för annons — paret (source, external_id).
- DB-002: TTL seen_listings.seen_at (dedup utan Redis).
- DB-003: TTL listings.fetched_at (auto-rensning).
- DB-006: MongoDB som replica set (för Change Streams; Atlas — direkt ur lådan).

Initiering av index på riktig DB:  python -m shared.db
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from shared.config import get_settings

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
    from pymongo import MongoClient
    from pymongo.database import Database

# Kollektionsnamn — enda källan, hårdkoda inte strängar i koden.
COLL_USERS = "users"
COLL_FILTERS = "filters"
COLL_LISTINGS = "listings"
COLL_NOTIFICATIONS = "notifications"
COLL_SEEN = "seen_listings"
COLL_AUDIT = "audit_log"


@lru_cache
def get_sync_client() -> MongoClient:
    """Synkron PyMongo-klient (för web/Flask)."""
    from pymongo import MongoClient

    return MongoClient(get_settings().mongo_uri)


def get_sync_db() -> Database:
    return get_sync_client()[get_settings().mongo_db]


@lru_cache
def get_async_client() -> AsyncIOMotorClient:
    """Asynkron Motor-klient (för poller/bot)."""
    from motor.motor_asyncio import AsyncIOMotorClient

    return AsyncIOMotorClient(get_settings().mongo_uri)


def get_async_db() -> AsyncIOMotorDatabase:
    return get_async_client()[get_settings().mongo_db]


def ensure_indexes(db: Database) -> None:
    """Skapa index och TTL (idempotent). Säkert att anropa flera gånger."""
    settings = get_settings()

    # users: unik e-mail
    db[COLL_USERS].create_index("email", unique=True, name="uniq_email")

    # filters: urval av användarens aktiva filter vid matchning
    db[COLL_FILTERS].create_index([("user_id", 1), ("is_active", 1)], name="user_active")

    # listings: unikt (source, external_id) [DB-001]; TTL via fetched_at [DB-003];
    # hjälpindex för matchning (typ/distrikt/pris).
    listings = db[COLL_LISTINGS]
    listings.create_index(
        [("source", 1), ("external_id", 1)], unique=True, name="uniq_source_extid"
    )
    listings.create_index(
        "fetched_at", expireAfterSeconds=settings.listings_ttl_days * 86400, name="ttl_fetched"
    )
    listings.create_index(
        [("listing_type", 1), ("district", 1), ("rent", 1)], name="match_type_district_rent"
    )

    # seen_listings: dedup (source, external_id) [BE-FL-003]; TTL via seen_at [DB-002]
    seen = db[COLL_SEEN]
    seen.create_index([("source", 1), ("external_id", 1)], unique=True, name="uniq_seen")
    seen.create_index("seen_at", expireAfterSeconds=settings.seen_ttl_hours * 3600, name="ttl_seen")

    # notifications: användarens historik efter tid + idempotens (en avisering
    # per paret (user, listing) — ett nytt poller-pass skapar inte dubbletter).
    notifications = db[COLL_NOTIFICATIONS]
    notifications.create_index([("user_id", 1), ("sent_at", -1)], name="user_sent")
    notifications.create_index(
        [("user_id", 1), ("listing_id", 1)], unique=True, name="uniq_user_listing"
    )

    # audit_log: efter tid
    db[COLL_AUDIT].create_index("created_at", name="created")


def init_indexes() -> list[str]:
    """Skapa index på konfigurerad DB och returnera listan över berörda kollektioner."""
    db = get_sync_db()
    ensure_indexes(db)
    return [COLL_USERS, COLL_FILTERS, COLL_LISTINGS, COLL_NOTIFICATIONS, COLL_SEEN, COLL_AUDIT]


if __name__ == "__main__":  # pragma: no cover
    settings = get_settings()
    print(f"Skapar index i DB '{settings.mongo_db}'…")
    for coll in init_indexes():
        print(f"  ✓ {coll}")
    print("Klart.")
