"""Tester för Bostadsförmedlingen-adaptern (kommunalt öppet data-API, Stockholm)."""

from __future__ import annotations

import httpx
import pytest
from poller.detector import classify
from poller.sources.bostadsformedlingen import BostadsformedlingenAdapter
from shared.models import ListingType, Source

ITEM = {
    "LägenhetId": 202601641,
    "AnnonsId": 292764,
    "Stadsdel": "Trångsund",
    "Gatuadress": "Trångsundsvägen 4C",
    "Kommun": "Huddinge",
    "AntalRum": 4,
    "Yta": 95,
    "Hyra": 20633,
    "Url": "/bostad/202601641/",
    "Lagenhetstyp": "Hyresrätt",
    "KoNamn": "Bostadskön",
}


def _adapter(handler) -> BostadsformedlingenAdapter:
    transport = httpx.MockTransport(handler)
    return BostadsformedlingenAdapter(client=httpx.AsyncClient(transport=transport))


def _ok(payload):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    return handler


async def test_normalizes_listing_as_queue():
    adapter = _adapter(_ok([ITEM]))
    listings = await adapter.fetch_listings()

    assert len(listings) == 1
    item = listings[0]
    assert item["source"] == Source.BOSTADSFORMEDLINGEN.value
    assert item["external_id"] == "202601641"
    assert item["title"] == "Trångsundsvägen 4C"
    assert item["url"] == "https://bostad.stockholm.se/bostad/202601641/"
    assert item["district"] == "Trångsund"
    assert item["rooms"] == 4.0
    assert item["area_m2"] == 95.0
    assert item["rent"] == 20633
    assert item["listing_type"] == ListingType.QUEUE.value  # köpoäng, inte FCFS
    assert item["fcfs"] is False
    assert "Bostadskön" in item["description"]
    await adapter.aclose()


async def test_queue_listing_classified_as_queue():
    adapter = _adapter(_ok([ITEM]))
    listings = await adapter.fetch_listings()
    assert classify(listings[0]) is ListingType.QUEUE
    await adapter.aclose()


async def test_item_without_id_skipped():
    bad = {"Gatuadress": "Utan id"}
    adapter = _adapter(_ok([bad, ITEM]))
    listings = await adapter.fetch_listings()
    assert [it["external_id"] for it in listings] == ["202601641"]
    await adapter.aclose()


async def test_5xx_raised_for_backoff():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={})

    adapter = _adapter(handler)
    with pytest.raises(httpx.HTTPStatusError):
        await adapter.fetch_listings()
    await adapter.aclose()


async def test_url_fallback_without_url_field():
    item = {k: v for k, v in ITEM.items() if k != "Url"}
    adapter = _adapter(_ok([item]))
    listings = await adapter.fetch_listings()
    assert listings[0]["url"] == "https://bostad.stockholm.se/bostad/202601641/"
    await adapter.aclose()
