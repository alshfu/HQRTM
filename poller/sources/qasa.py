"""Qasa-adapter (qasa.com) — publik marketplace-sökning (verifierad 2026-06-08).

Qasa exponerar en **publik, inloggningsfri** GraphQL-sökning på ``api.qasa.com/graphql``:
``homeIndexSearch { documents { nodes { ... } } }`` (samma som webbplatsens marketplace visar för
anonyma besökare). Schemat avstämt mot live-API → adaptern är ``enabled=True``.

Qasa-modell: uthyrning via ansökan (first/second-hand), **utan kö/köpoäng** → vi märker annonserna
som ``fcfs=True``. ``homeIndexSearch`` aggregerar även annonser från andra plattformar (fältet
``platform`` kan vara t.ex. ``blocket``); de hämtas lagligt via Qasas publika sökning.

Vid ändrat kontrakt rättas ENDAST denna fil (BE-DE-005).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from shared.config import get_settings
from shared.models import ListingType, Source

from poller.sources.base import SourceAdapter, as_float, as_int, extract_features
from poller.sources.registry import register

log = logging.getLogger("hqrtm.poller.qasa")

# Publik marketplace-sökning (anonym). Fält + argument avstämda mot live-API 2026-06-08/2026-06-10.
# ``params: HomeSearchParamsInput`` (bl.a. ``areaIdentifier: "se/<stad>"``) filtrerar per ort;
# ``documents(limit:)`` styr antalet. Utan ``areaIdentifier`` → hela landet.
_SEARCH_QUERY = """
query Q($params: HomeSearchParamsInput, $limit: Int) {
  homeIndexSearch(params: $params) {
    documents(limit: $limit) {
      nodes {
        id
        rent
        roomCount
        squareMeters
        firstHand
        homeType
        description
        platform
        currency
        location { locality route streetNumber }
        uploads { url type }
      }
    }
  }
}
"""


@register
class QasaAdapter(SourceAdapter):
    source = Source.QASA
    enabled = True  # publik anonym marketplace-sökning, schema verifierat

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client
        self._owns_client = client is None

    def _build_client(self) -> httpx.AsyncClient:
        s = get_settings()
        return httpx.AsyncClient(
            timeout=s.qasa_timeout_s,
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
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
        """Returnera färska Qasa-annonser, normaliserade till ``Listing``-fält.

        Om ``QASA_AREAS`` är satt hämtas varje ort separat (``areaIdentifier``) och resultaten
        slås ihop (dedup på ``id``). Tom konfig → en enda sökning över hela landet.
        """
        s = get_settings()
        areas = _parse_areas(s.qasa_areas)
        client = await self._get_client()
        currency = s.qasa_currency

        seen: set[str] = set()
        listings: list[dict] = []
        for area in areas:
            for node in await self._fetch_area(client, area, s):
                ext_id = node.get("id")
                if ext_id is None or str(ext_id) in seen:
                    continue
                # Begränsa till valt land via valuta (SEK = Sverige); Qasa täcker även FI/NO.
                if currency and node.get("currency") != currency:
                    continue
                seen.add(str(ext_id))
                listings.append(self._normalize(node))
        return listings

    async def _fetch_area(self, client: httpx.AsyncClient, area: str | None, s: Any) -> list[dict]:
        """Hämta råa noder för en ort (``area``) eller hela landet (``area=None``)."""
        params: dict[str, Any] = {}
        if area:
            params["areaIdentifier"] = area
        variables = {"params": params, "limit": s.qasa_fetch_amount}
        resp = await client.post(
            s.qasa_api_url, json={"query": _SEARCH_QUERY, "variables": variables}
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

        return (
            ((payload.get("data") or {}).get("homeIndexSearch") or {}).get("documents") or {}
        ).get("nodes") or []

    def _normalize(self, node: dict[str, Any]) -> dict:
        """Qasa-dokument → dict med fält från modellen ``Listing`` (+ ``fcfs`` för detektorn)."""
        ext_id = str(node["id"])
        loc = node.get("location") or {}
        title = self._title(loc)
        description = node.get("description")
        doc = {
            "source": str(self.source),
            "external_id": ext_id,
            "title": title,
            "url": f"{get_settings().qasa_public_base.rstrip('/')}/p/{ext_id}",
            "image_url": _first_image(node),
            "description": description,
            "district": loc.get("locality"),
            "rooms": as_float(node.get("roomCount")),
            "area_m2": as_float(node.get("squareMeters")),
            "rent": as_int(node.get("rent")),
            # Qasa har ingen köpoäng → ansökningsbaserad, behandlas som FCFS.
            "listing_type": ListingType.FCFS.value,
            "fcfs": True,
        }
        doc.update(extract_features(title, description))  # balkong/kök/våning ur texten
        return doc

    def _title(self, loc: dict) -> str:
        route = loc.get("route")
        number = loc.get("streetNumber")
        street = f"{route} {number}" if route and number else route
        parts = [p for p in (street, loc.get("locality")) if p]
        return ", ".join(parts) if parts else "Bostad"


def _parse_areas(raw: str) -> list[str | None]:
    """``"se/goteborg, se/stockholm"`` → ``["se/goteborg", "se/stockholm"]``; tomt → ``[None]``."""
    areas = [a.strip() for a in (raw or "").split(",") if a.strip()]
    return areas or [None]


def _first_image(node: dict[str, Any]) -> str | None:
    """Första bild-URL ur ``uploads`` (föredra type=home_picture)."""
    uploads = node.get("uploads") or []
    pics = [u for u in uploads if isinstance(u, dict) and u.get("url")]
    for u in pics:
        if u.get("type") == "home_picture":
            return u["url"]
    return pics[0]["url"] if pics else None
