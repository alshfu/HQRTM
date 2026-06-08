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

from poller.sources.base import SourceAdapter, as_float, as_int
from poller.sources.registry import register

log = logging.getLogger("hqrtm.poller.qasa")

# Publik marketplace-sökning (anonym). Fält avstämda mot live-API 2026-06-08.
_SEARCH_QUERY = """
{
  homeIndexSearch {
    documents {
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
        """Returnera färska Qasa-annonser, normaliserade till ``Listing``-fält."""
        s = get_settings()
        client = await self._get_client()
        resp = await client.post(s.qasa_api_url, json={"query": _SEARCH_QUERY})

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

        nodes = (
            ((payload.get("data") or {}).get("homeIndexSearch") or {}).get("documents") or {}
        ).get("nodes") or []
        # Begränsa till valt land via valuta (SEK = Sverige); Qasa täcker även FI/NO.
        currency = s.qasa_currency
        return [
            self._normalize(n)
            for n in nodes
            if n.get("id") is not None and (not currency or n.get("currency") == currency)
        ]

    def _normalize(self, node: dict[str, Any]) -> dict:
        """Qasa-dokument → dict med fält från modellen ``Listing`` (+ ``fcfs`` för detektorn)."""
        ext_id = str(node["id"])
        loc = node.get("location") or {}
        return {
            "source": str(self.source),
            "external_id": ext_id,
            "title": self._title(loc),
            "url": f"{get_settings().qasa_public_base.rstrip('/')}/p/{ext_id}",
            "image_url": _first_image(node),
            "description": node.get("description"),
            "district": loc.get("locality"),
            "rooms": as_float(node.get("roomCount")),
            "area_m2": as_float(node.get("squareMeters")),
            "rent": as_int(node.get("rent")),
            # Qasa har ingen köpoäng → ansökningsbaserad, behandlas som FCFS.
            "listing_type": ListingType.FCFS.value,
            "fcfs": True,
        }

    def _title(self, loc: dict) -> str:
        route = loc.get("route")
        number = loc.get("streetNumber")
        street = f"{route} {number}" if route and number else route
        parts = [p for p in (street, loc.get("locality")) if p]
        return ", ".join(parts) if parts else "Bostad"


def _first_image(node: dict[str, Any]) -> str | None:
    """Första bild-URL ur ``uploads`` (föredra type=home_picture)."""
    uploads = node.get("uploads") or []
    pics = [u for u in uploads if isinstance(u, dict) and u.get("url")]
    for u in pics:
        if u.get("type") == "home_picture":
            return u["url"]
    return pics[0]["url"] if pics else None
