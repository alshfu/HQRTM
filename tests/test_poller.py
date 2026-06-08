"""Tester av pollerkärnan (Fas 2, M1): FCFS-detektor, dedup, engine, async-loop."""

from __future__ import annotations

from poller.detector import classify, is_fcfs
from poller.engine import process_new_listings
from poller.main import current_interval_ms, run_once
from poller.sources.base import SourceAdapter
from shared.db import COLL_LISTINGS, COLL_SEEN
from shared.models import ListingType, Source

# ------------------------------------------------------------------- detector


def test_classify_explicit_type():
    assert classify({"listing_type": "fcfs"}) is ListingType.FCFS
    assert classify({"listing_type": "queue"}) is ListingType.QUEUE


def test_classify_boolean_flag():
    assert classify({"fcfs": True}) is ListingType.FCFS
    assert classify({"fcfs": False}) is ListingType.QUEUE


def test_classify_swedish_text_markers():
    assert is_fcfs({"title": "2 rok Söder — Först till kvarn"})
    assert (
        classify({"title": "Lägenhet", "description": "Krav: köpoäng och kötid"})
        is ListingType.QUEUE
    )
    assert classify({"title": "Vanlig annons"}) is ListingType.UNKNOWN


# ------------------------------------------------------------------- dedup + engine


def test_process_filters_queue_and_dedups(db):
    raw = [
        {"source": "homeq", "external_id": "a", "title": "Först till kvarn", "url": "u"},
        {
            "source": "homeq",
            "external_id": "b",
            "title": "Kötid krävs",
            "url": "u",
        },  # queue → bortsållas
        {"source": "homeq", "external_id": "a", "title": "Först till kvarn", "url": "u"},  # dublett
        {
            "source": "qasa",
            "external_id": "a",
            "fcfs": True,
            "title": "x",
            "url": "u",
        },  # annan källa
    ]
    new = process_new_listings(db, raw)
    ext_ids = {(n["source"], n["external_id"]) for n in new}
    assert ext_ids == {("homeq", "a"), ("qasa", "a")}  # FCFS, utan dublett; queue bortsållad
    assert all(n["listing_type"] == "fcfs" for n in new)
    # i listings sparas endast FCFS
    assert db[COLL_LISTINGS].count_documents({}) == 2
    # upprepad körning av samma batch → inget nytt (dedup)
    assert process_new_listings(db, raw) == []


def test_invalid_records_skipped(db):
    new = process_new_listings(db, [{"title": "no ids"}, {"source": "homeq"}])
    assert new == []
    assert db[COLL_SEEN].count_documents({}) == 0


# ------------------------------------------------------------------- async loop


class _FakeAdapter(SourceAdapter):
    source = Source.HOMEQ
    enabled = True

    def __init__(self, items):
        self._items = items

    async def fetch_listings(self):
        return self._items


async def test_run_once_collects_fcfs(db):
    adapter = _FakeAdapter(
        [
            {"external_id": "1", "title": "Först till kvarn", "url": "u"},
            {"external_id": "2", "title": "köpoäng", "url": "u"},
        ]
    )
    new = await run_once(db, [adapter])
    assert len(new) == 1
    assert new[0]["external_id"] == "1"
    assert new[0]["source"] == "homeq"  # satt från adapter.source


# ------------------------------------------------------------------- adaptive interval


def test_interval_day_vs_night():
    # HOT_HOURS standard 08-22: på dagen basintervall, på natten mer sällan
    day = current_interval_ms(12)
    night = current_interval_ms(3)
    assert night > day
