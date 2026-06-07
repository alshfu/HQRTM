"""Тесты адаптера Qasa (GraphQL, Фаза 2).

⚠️ Контракт Qasa не верифицирован официально — тесты фиксируют ту форму ответа, под
которую написан адаптер (см. poller/sources/qasa.py). Перед включением — сверить с живым API.
HTTP мокируется через httpx.MockTransport (без сети).
"""

from __future__ import annotations

import httpx
import pytest
from poller.detector import classify, is_fcfs
from poller.sources.qasa import QasaAdapter
from shared.models import ListingType, Source

HOME = {
    "id": "home-777",
    "slug": "soder-2a",
    "rent": 12500,
    "roomCount": 2,
    "squareMeters": 48,
    "rentalType": "long_term",
    "firstHand": True,
    "location": {"locality": "Stockholm", "route": "Götgatan", "streetNumber": "5"},
}


def _adapter(handler) -> QasaAdapter:
    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    return QasaAdapter(client=client)


def _graphql_ok(homes: list[dict]):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": {"homes": {"nodes": homes}}})

    return handler


async def test_fetch_normalizes_home_to_fcfs():
    adapter = _adapter(_graphql_ok([HOME]))
    listings = await adapter.fetch_listings()

    assert len(listings) == 1
    item = listings[0]
    assert item["source"] == Source.QASA.value
    assert item["external_id"] == "home-777"
    assert item["title"] == "Götgatan, Stockholm"
    assert item["url"] == "https://qasa.com/home/soder-2a"
    assert item["district"] == "Stockholm"
    assert item["rooms"] == 2.0
    assert item["area_m2"] == 48.0
    assert item["rent"] == 12500
    assert item["listing_type"] == ListingType.FCFS.value
    assert item["fcfs"] is True
    await adapter.aclose()


async def test_graphql_query_sends_first_variable():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        captured.update(json.loads(request.content))
        return httpx.Response(200, json={"data": {"homes": {"nodes": []}}})

    adapter = _adapter(handler)
    await adapter.fetch_listings()
    assert "homes" in captured["query"]
    assert captured["variables"]["first"] == 50  # qasa_fetch_amount по умолчанию
    await adapter.aclose()


async def test_url_falls_back_to_id_without_slug():
    home = {**HOME, "slug": None}
    adapter = _adapter(_graphql_ok([home]))
    listings = await adapter.fetch_listings()
    assert listings[0]["url"] == "https://qasa.com/home/home-777"
    await adapter.aclose()


async def test_non_first_hand_marked_queue():
    home = {**HOME, "firstHand": False}
    adapter = _adapter(_graphql_ok([home]))
    listings = await adapter.fetch_listings()
    assert listings[0]["listing_type"] == ListingType.QUEUE.value
    assert listings[0]["fcfs"] is False
    await adapter.aclose()


async def test_nodes_without_id_skipped():
    adapter = _adapter(_graphql_ok([{"slug": "x"}, HOME]))
    listings = await adapter.fetch_listings()
    assert [item["external_id"] for item in listings] == ["home-777"]
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
    adapter = _adapter(_graphql_ok([HOME]))
    listings = await adapter.fetch_listings()
    assert classify(listings[0]) is ListingType.FCFS
    assert is_fcfs(listings[0]) is True
    await adapter.aclose()
