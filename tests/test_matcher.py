"""Tester av filtermatchning och köläggning av aviseringar (Fas 2, BE-FL-004/005)."""

from __future__ import annotations

from poller.engine import enqueue_notifications, process_new_listings
from poller.matcher import match_users, matches
from shared.db import COLL_FILTERS, COLL_NOTIFICATIONS
from shared.models import ListingType

FCFS = ListingType.FCFS.value

LISTING = {
    "source": "homeq",
    "external_id": "1",
    "title": "2:a Söder",
    "url": "u",
    "district": "Stockholm",
    "rooms": 2.0,
    "area_m2": 55.0,
    "rent": 11000,
    "listing_type": FCFS,
}


# ------------------------------------------------------------------- matches() unit


def test_matches_empty_filter_matches_any_fcfs():
    assert matches({"only_fcfs": True}, LISTING) is True


def test_only_fcfs_rejects_queue():
    queue = {**LISTING, "listing_type": ListingType.QUEUE.value}
    assert matches({"only_fcfs": True}, queue) is False
    assert matches({"only_fcfs": False}, queue) is True


def test_rent_range():
    assert matches({"rent_min": 10000, "rent_max": 12000}, LISTING) is True
    assert matches({"rent_max": 10000}, LISTING) is False
    assert matches({"rent_min": 12000}, LISTING) is False


def test_rooms_and_area_range():
    assert matches({"rooms_min": 2, "rooms_max": 3}, LISTING) is True
    assert matches({"rooms_min": 3}, LISTING) is False
    assert matches({"area_min": 50, "area_max": 60}, LISTING) is True
    assert matches({"area_max": 40}, LISTING) is False


def test_missing_value_fails_bounded_filter():
    no_rent = {**LISTING, "rent": None}
    assert matches({"rent_max": 12000}, no_rent) is False
    assert matches({}, no_rent) is True  # utan gräns — släpps igenom


def test_sources_constraint():
    assert matches({"sources": ["qasa"]}, LISTING) is False
    assert matches({"sources": ["homeq", "qasa"]}, LISTING) is True
    assert matches({"sources": None}, LISTING) is True


def test_district_substring_case_insensitive():
    assert matches({"district": "stockholm"}, LISTING) is True
    assert matches({"district": "Göteborg"}, LISTING) is False
    # city som fallback mot samma fält district i annonsen
    assert matches({"city": "STOCK"}, LISTING) is True


def test_floor_range_is_lenient_on_unknown():
    on_3 = {**LISTING, "floor": 3}
    assert matches({"floor_min": 2, "floor_max": 5}, on_3) is True
    assert matches({"floor_min": 4}, on_3) is False  # känd våning utanför → ingen match
    # okänd våning (None) släpps igenom (maximerar matchningar)
    assert matches({"floor_min": 4}, LISTING) is True


def test_require_balcony_strict():
    with_balcony = {**LISTING, "has_balcony": True}
    without = {**LISTING, "has_balcony": False}
    assert matches({"require_balcony": True}, with_balcony) is True
    assert matches({"require_balcony": True}, without) is False
    # okänt (None) räknas inte som bekräftad balkong → ingen match vid krav
    assert matches({"require_balcony": True}, LISTING) is False
    # utan krav spelar fältet ingen roll
    assert matches({"require_balcony": False}, without) is True


def test_require_kitchen_strict():
    assert matches({"require_kitchen": True}, {**LISTING, "has_kitchen": True}) is True
    assert matches({"require_kitchen": True}, LISTING) is False


# ------------------------------------------------------------------- match_users()


def test_match_users_returns_matching_unique(db):
    db[COLL_FILTERS].insert_many(
        [
            {"user_id": "u1", "is_active": True, "rent_max": 12000},  # match
            {"user_id": "u1", "is_active": True, "rooms_min": 2},  # match (samma användare)
            {"user_id": "u2", "is_active": True, "rent_max": 9000},  # no match (för dyrt)
            {"user_id": "u3", "is_active": False, "rent_max": 12000},  # inaktiv
            {"user_id": "u4", "is_active": True, "sources": ["qasa"]},  # annan källa
        ]
    )
    assert match_users(db, LISTING) == ["u1"]  # unik, endast matchande aktiv


def test_match_users_source_none_matches(db):
    db[COLL_FILTERS].insert_one({"user_id": "u9", "is_active": True, "sources": None})
    assert match_users(db, LISTING) == ["u9"]


# ------------------------------------------------------------------- enqueue


def _seed_listing(db) -> dict:
    raw = [{**LISTING}]
    docs = process_new_listings(db, raw)
    assert len(docs) == 1
    return docs[0]


def test_enqueue_creates_queued_notifications(db):
    db[COLL_FILTERS].insert_many(
        [
            {"user_id": "u1", "is_active": True, "rent_max": 12000},
            {"user_id": "u2", "is_active": True},
        ]
    )
    doc = _seed_listing(db)
    created = enqueue_notifications(db, [doc])

    assert created == 2
    notifs = list(db[COLL_NOTIFICATIONS].find({}))
    assert {n["user_id"] for n in notifs} == {"u1", "u2"}
    assert all(n["status"] == "queued" for n in notifs)
    assert all(n["listing_id"] == str(doc["_id"]) for n in notifs)
    assert all(n["latency_ms"] is None for n in notifs)  # leverans — Fas 3


def test_enqueue_idempotent(db):
    db[COLL_FILTERS].insert_one({"user_id": "u1", "is_active": True})
    doc = _seed_listing(db)

    assert enqueue_notifications(db, [doc]) == 1
    assert enqueue_notifications(db, [doc]) == 0  # upprepning skapar inga dubletter
    assert db[COLL_NOTIFICATIONS].count_documents({}) == 1


def test_enqueue_no_match_no_notifications(db):
    db[COLL_FILTERS].insert_one({"user_id": "u1", "is_active": True, "rent_max": 5000})
    doc = _seed_listing(db)
    assert enqueue_notifications(db, [doc]) == 0
    assert db[COLL_NOTIFICATIONS].count_documents({}) == 0
