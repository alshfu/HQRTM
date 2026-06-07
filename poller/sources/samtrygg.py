"""Адаптер Samtrygg (samtrygg.se) — «trygg» андхандсутхюрнинг (аренда по заявке).

Контракт — публичная SwaggerHub-спека `Samtryg/Samtrygg/1.0.0`:
`GET /GetHomePageObjects` → массив объектов, сгруппированных по городам
(`RentalPropertyInfo`: `cityName`, `vacantAccomadationCount` + вложенный список
`RentalObjectInfo`). Поля объекта: `address`, `price`, `sqareMeters` (так в API — с опечаткой),
`startDate`, `endDate`, `imageUrl`, `rentalObjectLink`.

⚠️ В спеке **не задан host** и нет полей `id`/`rooms`/`title`. Поэтому:
- ``enabled=False`` — host и условия доступа/ToS не подтверждены; включение — за владельцем
  (см. COMPLIANCE.md). Перед включением: уточнить базовый URL (`SAMTRYGG_API_URL`) и ToS.
- `external_id` выводим из `rentalObjectLink` (или `address`) — стабильного id в ответе нет.
- Вложенный ключ со списком объектов в спеке назван `RentalObjectInfo`, но регистр/имя не
  гарантированы → парсим **защитно** (известные ключи, затем эвристика: list-поле, чьи элементы
  похожи на объект). При расхождении со схемой правится ТОЛЬКО этот файл (BE-DE-005).

Samtrygg — аренда по заявке (нет очереди/köpoäng) → объявления помечаем FCFS.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx
from shared.config import get_settings
from shared.models import ListingType, Source

from poller.sources.base import SourceAdapter
from poller.sources.registry import register

log = logging.getLogger("hqrtm.poller.samtrygg")

_NUM_RE = re.compile(r"\d+(?:[.,]\d+)?")
# «2 rum», «2 rok», «3 r o k», «1,5 rum» — число комнат в свободном тексте адреса/заголовка.
_ROOMS_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:r\.?o\.?k\.?|rum\b|rok\b|rms?\b)", re.IGNORECASE)

# Известные имена полей по спеке (+ возможные варианты регистра/синонимы) для устойчивости.
_LINK_KEYS = ("rentalObjectLink", "RentalObjectLink", "link", "url")
_ADDRESS_KEYS = ("address", "Address", "streetAddress")
_AREA_KEYS = ("sqareMeters", "squareMeters", "sqareMeter", "area", "size")
_PRICE_KEYS = ("price", "Price", "rent", "monthlyRent")
_NESTED_LIST_KEYS = ("RentalObjectInfo", "rentalObjectInfo", "rentalObjects", "objects")


@register
class SamtryggAdapter(SourceAdapter):
    source = Source.SAMTRYGG
    enabled = False  # host/ToS не подтверждены — включение за владельцем (COMPLIANCE.md)

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client
        self._owns_client = client is None

    def _build_client(self) -> httpx.AsyncClient:
        s = get_settings()
        return httpx.AsyncClient(
            timeout=s.samtrygg_timeout_s, headers={"Accept": "application/json"}
        )

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = self._build_client()
        return self._client

    async def aclose(self) -> None:
        if self._client is not None and self._owns_client:
            await self._client.aclose()
            self._client = None

    async def fetch_listings(self) -> list[dict]:
        """Вернуть нормализованные объявления Samtrygg (ключи — поля ``Listing``)."""
        s = get_settings()
        if not s.samtrygg_api_url:
            # Без подтверждённого host опрашивать нечего — тихо пропускаем (адаптер всё равно
            # enabled=False; защита на случай ручного включения без конфигурации URL).
            log.debug("samtrygg: SAMTRYGG_API_URL не задан — пропускаю опрос")
            return []

        client = await self._get_client()
        resp = await client.get(s.samtrygg_api_url)

        if resp.status_code == 429 or resp.status_code >= 500:
            retry_after = resp.headers.get("Retry-After")
            raise httpx.HTTPStatusError(
                f"Samtrygg {resp.status_code}"
                + (f" Retry-After={retry_after}" if retry_after else ""),
                request=resp.request,
                response=resp,
            )
        resp.raise_for_status()

        out: list[dict] = []
        for city_name, obj in _iter_objects(resp.json()):
            norm = self._normalize(obj, city_name)
            if norm is not None:
                out.append(norm)
        return out

    def _normalize(self, obj: dict[str, Any], city_name: str | None) -> dict | None:
        """Объект Samtrygg → dict с полями ``Listing`` (+ ``fcfs`` для детектора)."""
        link = _first(obj, _LINK_KEYS)
        address = _first(obj, _ADDRESS_KEYS)
        ext_id = link or address
        if not ext_id:
            return None  # без стабильного ключа дедуп невозможен — пропускаем

        title = self._title(address, city_name)
        return {
            "source": str(self.source),
            "external_id": str(ext_id),
            "title": title,
            "url": str(link or get_settings().samtrygg_public_base),
            "address": address,
            "district": city_name,
            "rooms": _rooms(address, title),
            "area_m2": _num(_first(obj, _AREA_KEYS), float),
            "rent": _num(_first(obj, _PRICE_KEYS), int),
            "listing_type": ListingType.FCFS.value,  # аренда по заявке, не очередь
            "fcfs": True,
        }

    def _title(self, address: str | None, city_name: str | None) -> str:
        first = address.split(",")[0].strip() if address else None
        parts = [p for p in (first, city_name) if p]
        return ", ".join(parts) if parts else "Bostad"


def _first(obj: dict[str, Any], keys: tuple[str, ...]) -> Any:
    """Первое непустое значение по списку возможных имён ключа (устойчиво к регистру/синонимам)."""
    for key in keys:
        value = obj.get(key)
        if value not in (None, ""):
            return value
    return None


def _iter_objects(payload: Any):
    """Защитно обойти ответ `GetHomePageObjects` → пары (cityName, объект).

    Структура: верхний список «городов», в каждом — `cityName` и вложенный список объектов
    (`RentalObjectInfo` по спеке). Берём известный ключ, иначе — первое list-поле, элементы
    которого похожи на объект (есть `address`/`price`/`rentalObjectLink`). Также поддержан
    «плоский» ответ — список самих объектов без группировки по городам.
    """
    groups = payload if isinstance(payload, list) else _coerce_list(payload)
    for group in groups:
        if not isinstance(group, dict):
            continue
        # Плоский список объектов (без обёртки-города): сам элемент — объявление.
        if any(k in group for k in _LINK_KEYS + _ADDRESS_KEYS) and not _has_object_list(group):
            yield None, group
            continue

        city = group.get("cityName") or group.get("city")
        for obj in _nested_objects(group):
            yield city, obj


def _coerce_list(payload: Any) -> list:
    """Достать список групп из объекта-обёртки (`results`/`data`/первое list-поле)."""
    if isinstance(payload, dict):
        for key in ("results", "data", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
        for value in payload.values():
            if isinstance(value, list):
                return value
    return []


def _has_object_list(group: dict) -> bool:
    return any(_looks_like_objects(group.get(k)) for k in _NESTED_LIST_KEYS) or any(
        _looks_like_objects(v) for v in group.values()
    )


def _nested_objects(group: dict):
    """Вернуть вложенный список объектов: известный ключ → иначе первое подходящее list-поле."""
    for key in _NESTED_LIST_KEYS:
        if _looks_like_objects(group.get(key)):
            return [o for o in group[key] if isinstance(o, dict)]
    for value in group.values():
        if _looks_like_objects(value):
            return [o for o in value if isinstance(o, dict)]
    return []


def _looks_like_objects(value: Any) -> bool:
    """list непустой, первый элемент — dict с признаками объявления."""
    return (
        isinstance(value, list)
        and bool(value)
        and isinstance(value[0], dict)
        and any(k in value[0] for k in _LINK_KEYS + _ADDRESS_KEYS + _PRICE_KEYS)
    )


def _rooms(*texts: str | None) -> float | None:
    """Из адреса/заголовка извлечь число комнат («2 rum», «3 rok», «1,5 rok») — None если нет."""
    for text in texts:
        if not text:
            continue
        m = _ROOMS_RE.search(text)
        if m:
            try:
                return float(m.group(1).replace(",", "."))
            except ValueError:
                continue
    return None


def _num(value: Any, cast):
    """Из строки вида '8 500 kr/mån' / '45 m²' извлечь число (None при отсутствии)."""
    if value is None:
        return None
    if isinstance(value, int | float):
        return cast(value)
    m = _NUM_RE.search(str(value).replace("\xa0", "").replace(" ", ""))
    if not m:
        return None
    try:
        return cast(float(m.group().replace(",", ".")))
    except (TypeError, ValueError):
        return None
