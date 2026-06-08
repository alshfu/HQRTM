"""Tester för bot.service (koppling + leverans), mongomock — utan aiogram/nätverk."""

from __future__ import annotations

from datetime import UTC, datetime

import mongomock
from bot.service import (
    latency_ms_for,
    link_by_code,
    mark_delivered,
    mark_failed,
    pending_notifications,
    render_message,
)
from shared.db import COLL_LISTINGS, COLL_NOTIFICATIONS, COLL_USERS


def _db():
    return mongomock.MongoClient()["t"]


def test_link_by_code_sets_chat_and_consumes_code():
    db = _db()
    db[COLL_USERS].insert_one({"email": "a@b.se", "link_code": "abc"})
    user = link_by_code(db, "abc", 555)
    assert user is not None
    assert user["telegram_chat_id"] == 555
    assert "link_code" not in user  # koden förbrukad
    assert link_by_code(db, "abc", 999) is None  # kan inte återanvändas


def test_link_by_code_invalid_or_empty():
    db = _db()
    assert link_by_code(db, "nope", 1) is None
    assert link_by_code(db, None, 1) is None


def test_pending_skips_unlinked_and_enriches():
    db = _db()
    linked = (
        db[COLL_USERS]
        .insert_one({"email": "l@x.se", "telegram_chat_id": 111, "locale": "sv"})
        .inserted_id
    )
    unlinked = db[COLL_USERS].insert_one({"email": "u@x.se"}).inserted_id
    lid = (
        db[COLL_LISTINGS]
        .insert_one({"title": "Storgatan 1", "url": "https://homeq.se/x", "district": "Göteborg"})
        .inserted_id
    )
    db[COLL_NOTIFICATIONS].insert_one(
        {"user_id": str(linked), "listing_id": str(lid), "status": "queued"}
    )
    db[COLL_NOTIFICATIONS].insert_one(
        {"user_id": str(unlinked), "listing_id": str(lid), "status": "queued"}
    )

    pend = pending_notifications(db)
    assert len(pend) == 1  # bara den kopplade användaren
    assert pend[0]["chat_id"] == 111
    assert pend[0]["listing"]["title"] == "Storgatan 1"


def test_mark_delivered_and_failed():
    db = _db()
    nid = db[COLL_NOTIFICATIONS].insert_one({"status": "queued"}).inserted_id
    mark_delivered(db, nid, 1234)
    n = db[COLL_NOTIFICATIONS].find_one({"_id": nid})
    assert n["status"] == "delivered" and n["latency_ms"] == 1234 and n["sent_at"] is not None

    nid2 = db[COLL_NOTIFICATIONS].insert_one({"status": "queued"}).inserted_id
    mark_failed(db, nid2, "boom")
    n2 = db[COLL_NOTIFICATIONS].find_one({"_id": nid2})
    assert n2["status"] == "failed" and "boom" in n2["error"]


def test_render_message_contains_essentials():
    msg = render_message(
        {
            "title": "Storgatan 1",
            "district": "Göteborg",
            "rooms": 2.0,
            "area_m2": 50.0,
            "rent": 9000,
            "url": "https://homeq.se/x",
            "fcfs": True,
        },
        "sv",
    )
    assert "Storgatan 1" in msg
    assert "https://homeq.se/x" in msg
    assert "2 rum" in msg and "9000 kr/mån" in msg
    assert "Först till kvarn" in msg


def test_latency_ms_for():
    past = datetime.now(UTC).replace(microsecond=0)
    assert latency_ms_for({"fetched_at": past}) >= 0
    assert latency_ms_for({}) is None
