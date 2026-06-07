"""Ядро обработки объявлений поллера (Фаза 2, веха M1).

Пайплайн на пачку нормализованных объявлений:
  дедуп (seen_listings) → классификация FCFS → отсев не-FCFS → upsert в listings.
Возвращает новые FCFS-объявления (для матчинга и рассылки — Фаза 3).
Логика синхронная (pymongo/mongomock); HTTP-конкурентность — в async-цикле main.py.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from shared.db import COLL_LISTINGS
from shared.models import ListingType

from poller.dedup import mark_seen
from poller.detector import classify

log = logging.getLogger("hqrtm.poller")


def process_new_listings(db, raw_listings: list[dict]) -> list[dict]:
    """Обработать пачку объявлений, вернуть новые FCFS."""
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
        db[COLL_LISTINGS].update_one(
            {"source": source, "external_id": external_id}, {"$set": doc}, upsert=True
        )
        new_fcfs.append(doc)

    if new_fcfs:
        log.info("Новых FCFS: %d", len(new_fcfs))
    return new_fcfs
