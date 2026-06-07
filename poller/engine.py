"""Ядро обработки объявлений поллера (Фаза 2).

Пайплайн на пачку нормализованных объявлений:
  дедуп (seen_listings) → классификация FCFS → отсев не-FCFS → upsert в listings →
  матчинг с фильтрами → постановка уведомлений (status=queued).
Возвращает новые FCFS-объявления; уведомления уже стоят в очереди (доставка — Фаза 3).
Логика синхронная (pymongo/mongomock); HTTP-конкурентность — в async-цикле main.py.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from pymongo.errors import DuplicateKeyError
from shared.db import COLL_LISTINGS, COLL_NOTIFICATIONS
from shared.models import ListingType, NotificationChannel, NotificationStatus

from poller.dedup import mark_seen
from poller.detector import classify
from poller.matcher import match_users

log = logging.getLogger("hqrtm.poller")


def process_new_listings(db, raw_listings: list[dict]) -> list[dict]:
    """Обработать пачку объявлений, вернуть новые FCFS (с проставленным `_id`)."""
    new_fcfs: list[dict] = []
    for item in raw_listings:
        source = item.get("source")
        external_id = item.get("external_id")
        if not source or not external_id:
            continue  # невалидная запись адаптера

        # дедуп: каждое объявление обрабатываем один раз (BE-FL-003)
        if not mark_seen(db, source, external_id):
            continue

        # детекция: дальше идут только FCFS (BE-FL-002)
        ltype = classify(item)
        if ltype is not ListingType.FCFS:
            continue

        doc = {**item, "listing_type": ListingType.FCFS.value, "fetched_at": datetime.now(UTC)}
        res = db[COLL_LISTINGS].update_one(
            {"source": source, "external_id": external_id}, {"$set": doc}, upsert=True
        )
        doc["_id"] = res.upserted_id or db[COLL_LISTINGS].find_one(
            {"source": source, "external_id": external_id}, {"_id": 1}
        ).get("_id")
        new_fcfs.append(doc)

    if new_fcfs:
        log.info("Новых FCFS: %d", len(new_fcfs))
    return new_fcfs


def enqueue_notifications(db, listings: list[dict]) -> int:
    """Матчинг новых FCFS с фильтрами → постановка уведомлений (status=queued).

    Идемпотентно: уникальный индекс (user_id, listing_id) не даёт дублей при повторном
    проходе. Доставка (Telegram) и проставление latency_ms — Фаза 3. Возвращает число
    созданных уведомлений.
    """
    created = 0
    for doc in listings:
        listing_id = doc.get("_id")
        if listing_id is None:
            continue
        listing_id = str(listing_id)
        for user_id in match_users(db, doc):
            if _enqueue(db, user_id, listing_id):
                created += 1
    if created:
        log.info("Поставлено уведомлений: %d", created)
    return created


def _enqueue(db, user_id: str, listing_id: str) -> bool:
    """Создать queued-уведомление, если его ещё нет. True — если создано."""
    notif = {
        "user_id": user_id,
        "listing_id": listing_id,
        "channel": NotificationChannel.TELEGRAM.value,
        "status": NotificationStatus.QUEUED.value,
        "latency_ms": None,
        "error": None,
        "sent_at": None,
    }
    try:
        res = db[COLL_NOTIFICATIONS].update_one(
            {"user_id": user_id, "listing_id": listing_id},
            {"$setOnInsert": notif},
            upsert=True,
        )
    except DuplicateKeyError:
        return False  # гонка: уже создано параллельно
    return res.upserted_id is not None
