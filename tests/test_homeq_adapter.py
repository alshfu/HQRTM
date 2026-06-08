"""Tester för HomeQ Core API-adaptern (Fas 2).

HTTP mockas via httpx.MockTransport — utan nätverk och tredjepartsberoenden.
Vi kontrollerar: auth-flöde, Card Search (FCFS-only), normalisering till Listing,
återinloggning vid 401, vidarebefordran av strypning 429, saknat konto, väg genom detektorn.
"""

from __future__ import annotations

import json

import httpx
import pytest
from poller.detector import classify, is_fcfs
from poller.sources.homeq import HomeQAdapter, HomeQAuthError
from shared.config import get_settings
from shared.models import ListingType, Source

CARD = {
    "id": 12345,
    "title": "2:a på Söder",
    "uri": "/bostad/12345",
    "city": "Stockholm",
    "municipality": "Stockholm",
    "rent": 11500,
    "rooms": 2.0,
    "area": 54.5,
    "image": "https://img.homeq.se/12345.jpg",
    "description": "Trevlig tvåa nära Medborgarplatsen.",
}


@pytest.fixture(autouse=True)
def _creds(monkeypatch):
    """Lägger in HomeQ-konto och rensar inställningscachen."""
    get_settings.cache_clear()
    monkeypatch.setenv("HOMEQ_USERNAME", "integration-bot")
    monkeypatch.setenv("HOMEQ_PASSWORD", "secret")
    monkeypatch.setenv("HOMEQ_PUBLIC_BASE", "https://homeq.se")
    yield
    get_settings.cache_clear()


def _adapter(handler) -> HomeQAdapter:
    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport, base_url="https://api.homeq.se")
    return HomeQAdapter(client=client)


async def test_auth_then_card_search_returns_normalized_fcfs():
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path == "/api/v2/tokens/":
            return httpx.Response(200, json={"token": "jwt-abc"})
        if request.url.path == "/api/v3/cards/":
            assert request.headers["Authorization"] == "JWT jwt-abc"
            return httpx.Response(200, json={"results": [CARD], "total_hits": 1})
        raise AssertionError(f"oväntad väg {request.url.path}")

    adapter = _adapter(handler)
    listings = await adapter.fetch_listings()

    assert calls == ["/api/v2/tokens/", "/api/v3/cards/"]
    assert len(listings) == 1
    item = listings[0]
    assert item["source"] == Source.HOMEQ.value
    assert item["external_id"] == "12345"
    assert item["title"] == "2:a på Söder"
    assert item["url"] == "https://homeq.se/bostad/12345"
    assert item["image_url"] == "https://img.homeq.se/12345.jpg"
    assert item["description"] == "Trevlig tvåa nära Medborgarplatsen."
    assert item["district"] == "Stockholm"
    assert item["rooms"] == 2.0
    assert item["area_m2"] == 54.5
    assert item["rent"] == 11500
    assert item["listing_type"] == ListingType.FCFS.value
    assert item["fcfs"] is True
    await adapter.aclose()


async def test_card_search_requests_fcfs_only():
    seen_body: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v2/tokens/":
            return httpx.Response(200, json={"token": "t"})
        import json

        seen_body.update(json.loads(request.content))
        return httpx.Response(200, json={"results": []})

    adapter = _adapter(handler)
    await adapter.fetch_listings()

    assert seen_body["first_come_first"] is True
    assert seen_body["queue_points"] is False
    assert seen_body["sorting"] == "publish_date.desc"
    assert seen_body["amount"] == get_settings().homeq_fetch_amount
    await adapter.aclose()


async def test_relogin_on_401():
    tokens = iter(["stale", "fresh"])
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path == "/api/v2/tokens/":
            return httpx.Response(200, json={"token": next(tokens)})
        # Första kortförfrågan med utgånget token → 401, sedan 200.
        if request.headers["Authorization"] == "JWT stale":
            return httpx.Response(401, json={"detail": "expired"})
        return httpx.Response(200, json={"results": [CARD]})

    adapter = _adapter(handler)
    listings = await adapter.fetch_listings()

    assert paths.count("/api/v2/tokens/") == 2  # återinloggning skedde
    assert len(listings) == 1
    await adapter.aclose()


async def test_throttling_429_is_raised_for_backoff():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v2/tokens/":
            return httpx.Response(200, json={"token": "t"})
        return httpx.Response(429, headers={"Retry-After": "30"}, json={})

    adapter = _adapter(handler)
    with pytest.raises(httpx.HTTPStatusError) as exc:
        await adapter.fetch_listings()
    assert "429" in str(exc.value)
    await adapter.aclose()


async def test_server_error_5xx_is_raised():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v2/tokens/":
            return httpx.Response(200, json={"token": "t"})
        return httpx.Response(503, json={})

    adapter = _adapter(handler)
    with pytest.raises(httpx.HTTPStatusError):
        await adapter.fetch_listings()
    await adapter.aclose()


async def test_missing_credentials_raises_auth_error(monkeypatch):
    monkeypatch.setenv("HOMEQ_USERNAME", "")
    monkeypatch.setenv("HOMEQ_PASSWORD", "")
    get_settings.cache_clear()

    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("får inte gå mot nätet utan konto")

    adapter = _adapter(handler)
    with pytest.raises(HomeQAuthError):
        await adapter.fetch_listings()
    await adapter.aclose()


async def test_auth_response_without_token_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"company": {"id": 1}})  # inget token

    adapter = _adapter(handler)
    with pytest.raises(HomeQAuthError):
        await adapter.fetch_listings()
    await adapter.aclose()


async def test_absolute_uri_and_fallback_url():
    cards = [
        {"id": 1, "title": "A", "uri": "https://x.se/ad/1"},  # absolut
        {"id": 2, "title": "B"},  # utan uri → fallback
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v2/tokens/":
            return httpx.Response(200, json={"token": "t"})
        return httpx.Response(200, json={"results": cards})

    adapter = _adapter(handler)
    listings = await adapter.fetch_listings()
    urls = {item["external_id"]: item["url"] for item in listings}
    assert urls["1"] == "https://x.se/ad/1"
    assert urls["2"] == "https://homeq.se/listing/2"
    await adapter.aclose()


async def test_cards_without_id_are_skipped():
    cards = [{"title": "no id"}, CARD]

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v2/tokens/":
            return httpx.Response(200, json={"token": "t"})
        return httpx.Response(200, json={"results": cards})

    adapter = _adapter(handler)
    listings = await adapter.fetch_listings()
    assert [item["external_id"] for item in listings] == ["12345"]
    await adapter.aclose()


async def test_normalized_listing_passes_detector_as_fcfs():
    """End-to-end-kontroll: ett normaliserat kort känns igen av detektorn som FCFS."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v2/tokens/":
            return httpx.Response(200, json={"token": "t"})
        return httpx.Response(200, json={"results": [CARD]})

    adapter = _adapter(handler)
    listings = await adapter.fetch_listings()
    assert classify(listings[0]) is ListingType.FCFS
    assert is_fcfs(listings[0]) is True
    await adapter.aclose()


# Inom respektive utanför Göteborgs bbox (publik anonym sökning).
_INSIDE = {
    "id": 1,
    "title": "Storgatan 1",
    "uri": "/lagenhet/1",
    "municipality": "Göteborg",
    "rent": 9000,
    "rooms": 2.0,
    "area": 50.0,
    "date_access": "2026-07-01",
    "location": {"lat": 57.70, "lon": 11.97},
    "images": [{"image": "https://media/1.jpg", "position": 0}],
}
_OUTSIDE = {
    "id": 2,
    "title": "Drottninggatan 5",
    "uri": "/lagenhet/2",
    "municipality": "Stockholm",
    "rent": 12000,
    "rooms": 1.0,
    "area": 30.0,
    "location": {"lat": 59.33, "lon": 18.06},
    "images": [],
}
_GBG_BBOX = (57.305, 57.9516, 11.2996, 12.6629)


async def test_public_cards_anonymous_filtered_by_bbox():
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("Authorization")
        body = json.loads(request.content)
        if body["offset"] == 0:
            return httpx.Response(200, json={"results": [_INSIDE, _OUTSIDE], "total_hits": 2})
        return httpx.Response(200, json={"results": []})

    adapter = _adapter(handler)
    listings = await adapter.fetch_public_cards(
        bbox=_GBG_BBOX, limit=10, page_size=200, max_pages=3
    )

    assert seen["auth"] is None  # anonym — ingen JWT
    assert [item["external_id"] for item in listings] == ["1"]  # bara den inom bbox
    item = listings[0]
    assert item["url"] == "https://homeq.se/lagenhet/1"
    assert item["image_url"] == "https://media/1.jpg"  # ur images-listan ({image: ...})
    assert "2 rum" in item["description"] and "Göteborg" in item["description"]  # syntetiserad
    await adapter.aclose()


async def test_public_cards_stops_at_limit():
    cards = [{**_INSIDE, "id": i, "uri": f"/lagenhet/{i}"} for i in range(1, 6)]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": cards, "total_hits": len(cards)})

    adapter = _adapter(handler)
    listings = await adapter.fetch_public_cards(bbox=_GBG_BBOX, limit=3, page_size=200, max_pages=5)
    assert len(listings) == 3
    await adapter.aclose()
