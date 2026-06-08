"""Integrationstester för skapande av index på mongomock (Fas 1)."""

from __future__ import annotations

import mongomock
import pytest
from shared.db import (
    COLL_LISTINGS,
    COLL_SEEN,
    COLL_USERS,
    ensure_indexes,
)


@pytest.fixture
def db():
    return mongomock.MongoClient()["hqrtm_test"]


def test_ensure_indexes_idempotent(db):
    # upprepat anrop ska inte krascha
    ensure_indexes(db)
    ensure_indexes(db)

    listings_idx = db[COLL_LISTINGS].index_information()
    assert "uniq_source_extid" in listings_idx
    assert listings_idx["uniq_source_extid"]["unique"] is True

    assert "uniq_email" in db[COLL_USERS].index_information()
    assert "uniq_seen" in db[COLL_SEEN].index_information()


def test_listing_uniqueness_per_source_external_id(db):
    ensure_indexes(db)
    listings = db[COLL_LISTINGS]
    listings.insert_one({"source": "homeq", "external_id": "x1", "title": "a"})

    # samma (source, external_id) — dubblett förbjuden
    with pytest.raises(Exception):  # noqa: B017  (mongomock → DuplicateKeyError)
        listings.insert_one({"source": "homeq", "external_id": "x1", "title": "b"})

    # samma external_id, men annan plattform — tillåtet (aggregator)
    listings.insert_one({"source": "qasa", "external_id": "x1", "title": "c"})
    assert listings.count_documents({"external_id": "x1"}) == 2
