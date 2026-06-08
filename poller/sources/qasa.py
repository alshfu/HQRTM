"""Qasa-adapter (qasa.com) — andra plattformen i Qasa Group (samma grupp som äger HomeQ).

⚠️ **KONTRAKTET ÄR INTE VERIFIERAT.** Till skillnad från HomeQ Core API har Qasa inget
publikt dokumenterat partner-API. Deras frontend använder en GraphQL-endpoint
(`api.qasa.com/graphql`, förfrågan `homes`), men den är inte dokumenterad för tredje part, och
ToS för programmatisk åtkomst är inte bekräftad. Därför:

* ``enabled=False`` — pollern bevakar inte adaptern; aktivering — endast efter avstämning av
  schemat mot live-API och bekräftad ToS av ägaren (se COMPLIANCE.md, Qasa = ❌).
* Förfrågan/normalisering nedan är skrivna efter den mest sannolika formen av GraphQL `homes`
  och är **defensiva** (allt via ``.get()``) — vid avvikelse mot schemat ändras ENDAST denna
  fil (BE-DE-005). Innan aktivering: stäm av fältnamnen i GraphQL-svaret och justera vid behov
  förfrågan `_HOMES_QUERY` och `_normalize`.

Qasa-modell: marketplace-uthyrning via ansökan (first-hand/second-hand), utan kö/köpoäng —
det ligger närmare FCFS («ansökte — hyresvärden väljer»), därför märker vi annonserna med
``fcfs=True`` (detektorn släpper dem vidare), om de inte uttryckligen är märkta som annat.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from shared.config import get_settings
from shared.models import ListingType, Source

from poller.sources.base import SourceAdapter, as_float, as_int, pick_image
from poller.sources.registry import register

log = logging.getLogger("hqrtm.poller.qasa")

# GraphQL-förfrågan om färska annonser. Fältnamn — best-effort (se varningen i modulen).
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
      description
      displayImage
      location { locality route streetNumber }
    }
  }
}
"""


@register
class QasaAdapter(SourceAdapter):
    source = Source.QASA
    enabled = False  # kontraktet ej verifierat + ToS ej bekräftad — ägarens beslut

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
        """Returnera färska Qasa-annonser, normaliserade till ``Listing``-fält."""
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
        """Qasa-nod `home` → dict med fält från modellen ``Listing`` (+ ``fcfs`` för detektorn)."""
        ext_id = str(node["id"])
        loc = node.get("location") or {}
        # Qasa — uthyrning via ansökan (ingen köpoäng) → tolkas som FCFS, om inte annat anges.
        is_fcfs = node.get("firstHand") is not False
        return {
            "source": str(self.source),
            "external_id": ext_id,
            "title": self._title(node, loc),
            "url": self._listing_url(node, ext_id),
            "image_url": node.get("displayImage") or pick_image(node),
            "description": node.get("description"),
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
