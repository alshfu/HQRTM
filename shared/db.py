"""Подключение к MongoDB и создание индексов.

Два клиента:
- PyMongo (синхронный) — для Flask (web).
- Motor (асинхронный) — для поллера и бота.

Индексы (Фаза 1) реализуют инварианты модели данных (Roadmap §3):
DB-001 unique listings.external_id · DB-002 TTL seen_listings ·
DB-003 TTL listings · DB-006 replica set.
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from shared.config import get_settings

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
    from pymongo import MongoClient
    from pymongo.database import Database


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
    """Создать индексы и TTL (идемпотентно). Реализуется в Фазе 1.

    TODO(Фаза 1):
      - listings: unique(external_id) [DB-001]; TTL(fetched_at, ~7 дней) [DB-003]
      - seen_listings: TTL(seen_at, ~24 ч) [DB-002]
      - users: unique(email)
      - filters: index(user_id, is_active)
      - notifications: index(user_id, sent_at)
    """
    raise NotImplementedError("ensure_indexes() — Фаза 1")
