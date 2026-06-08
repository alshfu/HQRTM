"""Bakgrundslyssnare för MongoDB Change Stream på samlingen notifications (Fas 6).

För varje ny avisering (insert) publiceras en händelse med listing-data till brokern,
adresserat till prenumeranterna för motsvarande user_id. Kräver replica set (Atlas — direkt);
om Change Streams inte är tillgängliga avslutas tråden och klienterna använder fallback-polling.
"""

from __future__ import annotations

import logging
import threading

from shared.db import COLL_LISTINGS, COLL_NOTIFICATIONS

from web.db import serialize
from web.sse.broker import broker

log = logging.getLogger("hqrtm.sse")

_started = False
_lock = threading.Lock()


def _build_event(db, notification: dict) -> dict:
    listing = None
    listing_id = notification.get("listing_id")
    if listing_id:
        from bson import ObjectId
        from bson.errors import InvalidId

        try:
            listing = db[COLL_LISTINGS].find_one({"_id": ObjectId(listing_id)})
        except (InvalidId, TypeError):
            listing = None
    return {
        "type": "match",
        "notification": serialize(notification),
        "listing": serialize(listing),
    }


def _run(db) -> None:
    try:
        pipeline = [{"$match": {"operationType": "insert"}}]
        with db[COLL_NOTIFICATIONS].watch(pipeline, full_document="updateLookup") as stream:
            log.info("SSE change-stream watcher startad")
            for change in stream:
                doc = change.get("fullDocument") or {}
                user_id = str(doc.get("user_id")) if doc.get("user_id") else None
                if user_id:
                    broker.publish(user_id, _build_event(db, doc))
    except Exception as exc:  # noqa: BLE001 — inget fel får krascha web
        log.warning("SSE watcher stoppad: %s (fallback till polling hos klienter)", exc)


def ensure_watcher_started(db) -> None:
    """Starta watchern lat en gång per process (daemon-tråd)."""
    global _started
    with _lock:
        if _started:
            return
        _started = True
    threading.Thread(target=_run, args=(db,), daemon=True, name="sse-watcher").start()
