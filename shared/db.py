"""Подключение к MongoDB и создание индексов (Фаза 1).

Два клиента:
- PyMongo (синхронный) — для Flask (web).
- Motor (асинхронный) — для поллера и бота.

Индексы реализуют инварианты модели данных (Roadmap §3, расширено для мульти-source):
- DB-001: уникальность объявления — пара (source, external_id).
- DB-002: TTL seen_listings.seen_at (дедуп без Redis).
- DB-003: TTL listings.fetched_at (авто-очистка).
- DB-006: MongoDB как replica set (для Change Streams; Atlas — из коробки).

Инициализация индексов на реальной БД:  python -m shared.db
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from shared.config import get_settings

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
    from pymongo import MongoClient
    from pymongo.database import Database

# Имена коллекций — единый источник, не хардкодить строки в коде.
COLL_USERS = "users"
COLL_FILTERS = "filters"
COLL_LISTINGS = "listings"
COLL_NOTIFICATIONS = "notifications"
COLL_SEEN = "seen_listings"
COLL_AUDIT = "audit_log"


@lru_cache
def get_sync_client() -> MongoClient:
    """Синхронный клиент PyMongo (для web/Flask)."""
    from pymongo import MongoClient

    return MongoClient(get_settings().mongo_uri)


def get_sync_db() -> Database:
    return get_sync_client()[get_settings().mongo_db]


@lru_cache
def get_async_client() -> AsyncIOMotorClient:
    """Асинхронный клиент Motor (для poller/bot)."""
    from motor.motor_asyncio import AsyncIOMotorClient

    return AsyncIOMotorClient(get_settings().mongo_uri)


def get_async_db() -> AsyncIOMotorDatabase:
    return get_async_client()[get_settings().mongo_db]


def ensure_indexes(db: Database) -> None:
    """Создать индексы и TTL (идемпотентно). Безопасно вызывать многократно."""
    settings = get_settings()

    # users: уникальный e-mail
    db[COLL_USERS].create_index("email", unique=True, name="uniq_email")

    # filters: выборка активных фильтров пользователя при матчинге
    db[COLL_FILTERS].create_index([("user_id", 1), ("is_active", 1)], name="user_active")

    # listings: уникум (source, external_id) [DB-001]; TTL по fetched_at [DB-003];
    # вспомогательный индекс под матчинг (тип/район/цена).
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

    # seen_listings: дедуп (source, external_id) [BE-FL-003]; TTL по seen_at [DB-002]
    seen = db[COLL_SEEN]
    seen.create_index([("source", 1), ("external_id", 1)], unique=True, name="uniq_seen")
    seen.create_index("seen_at", expireAfterSeconds=settings.seen_ttl_hours * 3600, name="ttl_seen")

    # notifications: история пользователя по времени + идемпотентность (одно уведомление
    # на пару (user, listing) — повторный проход поллера не плодит дубли).
    notifications = db[COLL_NOTIFICATIONS]
    notifications.create_index([("user_id", 1), ("sent_at", -1)], name="user_sent")
    notifications.create_index(
        [("user_id", 1), ("listing_id", 1)], unique=True, name="uniq_user_listing"
    )

    # audit_log: по времени
    db[COLL_AUDIT].create_index("created_at", name="created")


def init_indexes() -> list[str]:
    """Создать индексы на настроенной БД и вернуть список затронутых коллекций."""
    db = get_sync_db()
    ensure_indexes(db)
    return [COLL_USERS, COLL_FILTERS, COLL_LISTINGS, COLL_NOTIFICATIONS, COLL_SEEN, COLL_AUDIT]


if __name__ == "__main__":  # pragma: no cover
    settings = get_settings()
    print(f"Создаю индексы в БД '{settings.mongo_db}'…")
    for coll in init_indexes():
        print(f"  ✓ {coll}")
    print("Готово.")
