"""Kärnan för pollerns annonsbearbetning (Fas 2).

Pipeline för en batch normaliserade annonser:
  dedup (seen_listings) → FCFS-klassificering → avskiljning av icke-FCFS → upsert i listings →
  matchning mot filter → kö av aviseringar (status=queued).
Returnerar nya FCFS-annonser; aviseringarna står redan i kö (utskick — Fas 3).
Logiken är synkron (pymongo/mongomock); HTTP-samtidighet — i async-loopen main.py.
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
    """Bearbeta en batch annonser, returnera nya FCFS (med satt `_id`)."""
    new_fcfs: list[dict] = []
    for item in raw_listings:
        source = item.get("source")
        external_id = item.get("external_id")
        if not source or not external_id:
            continue  # ogiltig post från adaptern

        # dedup: varje annons bearbetas en gång (BE-FL-003)
        if not mark_seen(db, source, external_id):
            continue

        # detektering: bara FCFS går vidare (BE-FL-002)
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
        log.info("Nya FCFS: %d", len(new_fcfs))
    return new_fcfs


def enqueue_notifications(db, listings: list[dict]) -> int:
    """Matchning av nya FCFS mot filter → kö av aviseringar (status=queued).

    Idempotent: unikt index (user_id, listing_id) ger inga dubbletter vid upprepad
    genomgång. Utskick (Telegram) och sättning av latency_ms — Fas 3. Returnerar antalet
    skapade aviseringar.
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
        log.info("Köade aviseringar: %d", created)
    return created


def _enqueue(db, user_id: str, listing_id: str) -> bool:
    """Skapa en queued-avisering om den inte redan finns. True — om skapad."""
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
        return False  # race: redan skapad parallellt
    return res.upserted_id is not None
