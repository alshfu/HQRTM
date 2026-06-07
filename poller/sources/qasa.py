"""Адаптер Qasa (qasa.com) — вторая площадка Qasa Group (та же группа, что владеет HomeQ).

⚠️ **КОНТРАКТ НЕ ВЕРИФИЦИРОВАН.** В отличие от HomeQ Core API, у Qasa нет публично
документированного партнёрского API. Их фронтенд использует GraphQL-эндпоинт
(`api.qasa.com/graphql`, запрос `homes`), но он не документирован для третьих лиц, а ToS на
программный доступ не подтверждён. Поэтому:

* ``enabled=False`` — поллер адаптер не опрашивает; включение — только после сверки схемы с
  живым API и подтверждения ToS владельцем (см. COMPLIANCE.md, Qasa = ❌).
* Запрос/нормализация ниже написаны по наиболее достоверной форме GraphQL `homes` и
  **защитны** (всё через ``.get()``) — при расхождении со схемой правится ТОЛЬКО этот файл
  (BE-DE-005). Перед включением: сверить имена полей в GraphQL-ответе и при необходимости
  скорректировать запрос `_HOMES_QUERY` и `_normalize`.

Модель Qasa: маркетплейс-аренда по заявке (first-hand/second-hand), без очереди/köpoäng —
это ближе к FCFS («подал заявку — арендодатель выбирает»), поэтому объявления помечаем
``fcfs=True`` (детектор пропустит их дальше), если явно не помечены как иное.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from shared.config import get_settings
from shared.models import ListingType, Source

from poller.sources.base import SourceAdapter, as_float, as_int
from poller.sources.registry import register

log = logging.getLogger("hqrtm.poller.qasa")

# GraphQL-запрос свежих объявлений. Имена полей — best-effort (см. предупреждение в модуле).
_HOMES_QUERY = """
query Homes($first: Int!) {
  homes(first: $first, order: { field: PUBLISHED_AT, direction: DESCENDING }) {
    nodes {
      id
      slug
      rent
      roomCount
      squareMeters
      rentalType
      firstHand
      location { locality route streetNumber }
    }
  }
}
"""


@register
class QasaAdapter(SourceAdapter):
    source = Source.QASA
    enabled = False  # контракт не верифицирован + ToS не подтверждён — решение владельца

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client
        self._owns_client = client is None

    def _build_client(self) -> httpx.AsyncClient:
        s = get_settings()
        return httpx.AsyncClient(
            timeout=s.qasa_timeout_s, headers={"Content-Type": "application/json"}
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
        """Вернуть свежие объявления Qasa, нормализованные в поля ``Listing``."""
        s = get_settings()
        client = await self._get_client()
        resp = await client.post(
            s.qasa_api_url,
            json={"query": _HOMES_QUERY, "variables": {"first": s.qasa_fetch_amount}},
        )

        if resp.status_code == 429 or resp.status_code >= 500:
            retry_after = resp.headers.get("Retry-After")
            raise httpx.HTTPStatusError(
                f"Qasa graphql {resp.status_code}"
                + (f" Retry-After={retry_after}" if retry_after else ""),
                request=resp.request,
                response=resp,
            )
        resp.raise_for_status()

        payload = resp.json()
        if payload.get("errors"):
            raise RuntimeError(f"Qasa GraphQL errors: {payload['errors']}")

        nodes = (payload.get("data") or {}).get("homes", {}).get("nodes") or []
        return [self._normalize(n) for n in nodes if n.get("id") is not None]

    def _normalize(self, node: dict[str, Any]) -> dict:
        """Узел Qasa `home` → dict с полями модели ``Listing`` (+ ``fcfs`` для детектора)."""
        ext_id = str(node["id"])
        loc = node.get("location") or {}
        # Qasa — аренда по заявке (нет köpoäng) → трактуем как FCFS, если явно не иное.
        is_fcfs = node.get("firstHand") is not False
        return {
            "source": str(self.source),
            "external_id": ext_id,
            "title": self._title(node, loc),
            "url": self._listing_url(node, ext_id),
            "district": loc.get("locality"),
            "rooms": as_float(node.get("roomCount")),
            "area_m2": as_float(node.get("squareMeters")),
            "rent": as_int(node.get("rent")),
            "listing_type": (ListingType.FCFS if is_fcfs else ListingType.QUEUE).value,
            "fcfs": is_fcfs,
        }

    def _title(self, node: dict, loc: dict) -> str:
        route = loc.get("route")
        locality = loc.get("locality")
        parts = [p for p in (route, locality) if p]
        return ", ".join(parts) if parts else "Bostad"

    def _listing_url(self, node: dict, ext_id: str) -> str:
        base = get_settings().qasa_public_base.rstrip("/")
        slug = node.get("slug")
        return f"{base}/home/{slug or ext_id}"
