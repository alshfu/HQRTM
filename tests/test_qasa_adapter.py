"""Tester för Qasa-adaptern (publik homeIndexSearch, schema verifierat 2026-06-08).

HTTP mockas via httpx.MockTransport (utan nätverk).
"""

from __future__ import annotations

import httpx
import pytest
from poller.detector import classify, is_fcfs
from poller.sources.qasa import QasaAdapter
from shared.models import ListingType, Source

NODE = {
    "id": "home-777",
    "rent": 12500,
    "roomCount": 2,
    "squareMeters": 48,
    "firstHand": False,
    "homeType": "apartment",
    "description": "Trevlig lägenhet.",
    "platform": "qasa",
    "location": {"locality": "Stockholm", "route": "Götgatan", "streetNumber": "5"},
    "uploads": [
        {"url": "https://img/floorplan.jpg", "type": "floor_plan"},
        {"url": "https://img/home.jpg", "type": "home_picture"},
    ],
}


def _adapter(handler) -> QasaAdapter:
    transport = httpx.MockTransport(handler)
    return QasaAdapter(client=httpx.AsyncClient(transport=transport))


def _ok(nodes):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"data": {"homeIndexSearch": {"documents": {"nodes": nodes}}}}
        )

    return handler


async def test_fetch_normalizes_to_fcfs():
    adapter = _adapter(_ok([NODE]))
    listings = await adapter.fetch_listings()

    assert len(listings) == 1
    item = listings[0]
    assert item["source"] == Source.QASA.value
    assert item["external_id"] == "home-777"
    assert item["title"] == "Götgatan 5, Stockholm"
    assert item["url"] == "https://qasa.com/p/home-777"
    assert item["image_url"] == "https://img/home.jpg"  # föredrar home_picture
    assert item["district"] == "Stockholm"
    assert item["rooms"] == 2.0
    assert item["area_m2"] == 48.0
    assert item["rent"] == 12500
    assert item["listing_type"] == ListingType.FCFS.value  # ingen köpoäng → FCFS
    assert item["fcfs"] is True
    await adapter.aclose()


async def test_nodes_without_id_skipped():
    adapter = _adapter(_ok([{"rent": 5}, NODE]))
    listings = await adapter.fetch_listings()
    assert [item["external_id"] for item in listings] == ["home-777"]
    await adapter.aclose()


async def test_image_falls_back_to_first_upload():
    node = {**NODE, "uploads": [{"url": "https://img/x.jpg", "type": "floor_plan"}]}
    adapter = _adapter(_ok([node]))
    listings = await adapter.fetch_listings()
    assert listings[0]["image_url"] == "https://img/x.jpg"
    await adapter.aclose()


async def test_graphql_errors_raise():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"errors": [{"message": "boom"}]})

    adapter = _adapter(handler)
    with pytest.raises(RuntimeError):
        await adapter.fetch_listings()
    await adapter.aclose()


async def test_throttling_429_raised_for_backoff():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"Retry-After": "30"}, json={})

    adapter = _adapter(handler)
    with pytest.raises(httpx.HTTPStatusError) as exc:
        await adapter.fetch_listings()
    assert "429" in str(exc.value)
    await adapter.aclose()


async def test_5xx_raised():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={})

    adapter = _adapter(handler)
    with pytest.raises(httpx.HTTPStatusError):
        await adapter.fetch_listings()
    await adapter.aclose()


async def test_normalized_passes_detector_as_fcfs():
    adapter = _adapter(_ok([NODE]))
    listings = await adapter.fetch_listings()
    assert classify(listings[0]) is ListingType.FCFS
    assert is_fcfs(listings[0]) is True
    await adapter.aclose()
