"""Тесты адаптера Samtrygg (GetHomePageObjects, Фаза 2).

⚠️ Host/контракт Samtrygg официально не подтверждён — тесты фиксируют форму ответа из публичной
SwaggerHub-спеки, под которую написан адаптер (см. poller/sources/samtrygg.py). HTTP мокируется
через httpx.MockTransport (без сети). Перед включением (enabled=True) — сверить с живым API.
"""

from __future__ import annotations

import httpx
import pytest
from poller.detector import classify, is_fcfs
from poller.sources.samtrygg import SamtryggAdapter
from shared.config import get_settings
from shared.models import ListingType, Source

# Ответ по спеке: список «городов», в каждом — cityName + вложенный список RentalObjectInfo.
OBJ = {
    "address": "Storgatan 1, 2 rok",
    "price": "8 500 kr/mån",
    "sqareMeters": "45 m²",
    "rentalObjectLink": "https://samtrygg.se/objekt/123",
    "imageUrl": "https://samtrygg.se/img/123.jpg",
}
CITY_GROUPED = [
    {"cityName": "Stockholm", "vacantAccomadationCount": 1, "RentalObjectInfo": [OBJ]},
]

API_URL = "https://api.samtrygg.test/GetHomePageObjects"


@pytest.fixture(autouse=True)
def _configure_url(monkeypatch):
    # Адаптер опрашивает только при заданном SAMTRYGG_API_URL — подставляем тестовый host.
    s = get_settings()
    monkeypatch.setattr(s, "samtrygg_api_url", API_URL, raising=False)
    yield


def _adapter(handler) -> SamtryggAdapter:
    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    return SamtryggAdapter(client=client)


def _ok(payload):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    return handler


async def test_fetch_normalizes_city_grouped_object():
    adapter = _adapter(_ok(CITY_GROUPED))
    listings = await adapter.fetch_listings()

    assert len(listings) == 1
    item = listings[0]
    assert item["source"] == Source.SAMTRYGG.value
    assert item["external_id"] == "https://samtrygg.se/objekt/123"
    assert item["title"] == "Storgatan 1, Stockholm"
    assert item["url"] == "https://samtrygg.se/objekt/123"
    assert item["district"] == "Stockholm"
    assert item["rooms"] == 2.0  # «2 rok» вытащено из адреса
    assert item["area_m2"] == 45.0  # «45 m²» → 45.0
    assert item["rent"] == 8500  # «8 500 kr/mån» → 8500
    assert item["listing_type"] == ListingType.FCFS.value
    assert item["fcfs"] is True
    await adapter.aclose()


async def test_flat_list_without_city_wrapper():
    adapter = _adapter(_ok([OBJ]))
    listings = await adapter.fetch_listings()
    assert len(listings) == 1
    assert listings[0]["external_id"] == "https://samtrygg.se/objekt/123"
    assert listings[0]["district"] is None
    await adapter.aclose()


async def test_wrapped_in_results_key():
    adapter = _adapter(_ok({"results": CITY_GROUPED}))
    listings = await adapter.fetch_listings()
    assert len(listings) == 1
    assert listings[0]["district"] == "Stockholm"
    await adapter.aclose()


async def test_external_id_falls_back_to_address():
    obj = {k: v for k, v in OBJ.items() if k != "rentalObjectLink"}
    adapter = _adapter(_ok([{"cityName": "Göteborg", "RentalObjectInfo": [obj]}]))
    listings = await adapter.fetch_listings()
    assert listings[0]["external_id"] == "Storgatan 1, 2 rok"
    # URL без ссылки откатывается к публичной базе.
    assert listings[0]["url"] == "https://samtrygg.se"
    await adapter.aclose()


async def test_object_without_id_or_address_skipped():
    bad = {"price": "5 000 kr", "sqareMeters": "20"}
    adapter = _adapter(_ok([{"cityName": "Malmö", "RentalObjectInfo": [bad, OBJ]}]))
    listings = await adapter.fetch_listings()
    assert [item["external_id"] for item in listings] == ["https://samtrygg.se/objekt/123"]
    await adapter.aclose()


async def test_rooms_none_when_absent():
    obj = {**OBJ, "address": "Storgatan 1"}  # нет «N rok» в адресе
    adapter = _adapter(_ok([{"cityName": "Uppsala", "RentalObjectInfo": [obj]}]))
    listings = await adapter.fetch_listings()
    assert listings[0]["rooms"] is None
    await adapter.aclose()


async def test_numeric_fields_parsed_from_numbers():
    obj = {**OBJ, "price": 9000, "sqareMeters": 52.5}
    adapter = _adapter(_ok([{"cityName": "Lund", "RentalObjectInfo": [obj]}]))
    listings = await adapter.fetch_listings()
    assert listings[0]["rent"] == 9000
    assert listings[0]["area_m2"] == 52.5
    await adapter.aclose()


async def test_no_api_url_skips_without_request(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "samtrygg_api_url", "", raising=False)

    def boom(request: httpx.Request) -> httpx.Response:  # не должен вызваться
        raise AssertionError("HTTP-запрос не должен уходить без SAMTRYGG_API_URL")

    adapter = _adapter(boom)
    assert await adapter.fetch_listings() == []
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
    adapter = _adapter(_ok(CITY_GROUPED))
    listings = await adapter.fetch_listings()
    assert classify(listings[0]) is ListingType.FCFS
    assert is_fcfs(listings[0]) is True
    await adapter.aclose()
