"""Adapter för Bostadsförmedlingen i Stockholm — kommunalt öppet data-API.

Publik JSON-lista: ``GET https://bostad.stockholm.se/AllaAnnonser/?vy=lista`` → lediga
lägenheter i Stockholmsregionen (samma data som myndighetens egen publika lista, ingen auth).
Bostadsförmedlingen är **kö-baserad** (köpoäng) → ``listing_type=queue``, ``fcfs=False``.

Offentlig myndighet som publicerar lediga lägenheter öppet → legitim källa, ``enabled=True``.
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

log = logging.getLogger("hqrtm.poller.bostadsformedlingen")


def _ext_id(item: dict[str, Any]) -> Any:
    return item.get("LägenhetId") or item.get("AnnonsId")


@register
class BostadsformedlingenAdapter(SourceAdapter):
    source = Source.BOSTADSFORMEDLINGEN
    enabled = True  # publik öppen kommunal data, ingen auth/ToS-blockerare

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client
        self._owns_client = client is None

    def _build_client(self) -> httpx.AsyncClient:
        s = get_settings()
        return httpx.AsyncClient(
            timeout=s.bostadsformedlingen_timeout_s,
            headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"},
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
        """Hämtar lediga lägenheter från Bostadsförmedlingen, normaliserade till ``Listing``."""
        s = get_settings()
        client = await self._get_client()
        resp = await client.get(s.bostadsformedlingen_api_url)

        if resp.status_code == 429 or resp.status_code >= 500:
            retry_after = resp.headers.get("Retry-After")
            raise httpx.HTTPStatusError(
                f"Bostadsförmedlingen {resp.status_code}"
                + (f" Retry-After={retry_after}" if retry_after else ""),
                request=resp.request,
                response=resp,
            )
        resp.raise_for_status()

        data = resp.json()
        items = data if isinstance(data, list) else data.get("results", [])
        return [self._normalize(it) for it in items if _ext_id(it) is not None]

    def _normalize(self, it: dict[str, Any]) -> dict:
        title = it.get("Gatuadress") or "Bostad"
        description = self._desc(it)
        balcony = it.get("Balkong")
        doc = {
            "source": str(self.source),
            "external_id": str(_ext_id(it)),
            "title": title,
            "url": self._url(it),
            "image_url": None,
            "description": description,
            "district": it.get("Stadsdel") or it.get("Kommun"),
            "rooms": as_float(it.get("AntalRum")),
            "area_m2": as_float(it.get("Yta")),
            "rent": as_int(it.get("Hyra")),
            # Strukturerade fält från det öppna API:et (auktoritativa, inkl. False).
            "floor": as_int(it.get("Vaning")),
            "has_balcony": balcony if isinstance(balcony, bool) else None,
            "listing_type": ListingType.QUEUE.value,  # köpoäng, inte FCFS
            "fcfs": False,
        }
        # Komplettera saknade fält (t.ex. kök) ur texten — skriv inte över strukturerad källdata.
        for key, val in extract_features(title, description).items():
            if doc.get(key) is None:
                doc[key] = val
        return doc

    def _url(self, it: dict[str, Any]) -> str:
        base = get_settings().bostadsformedlingen_public_base.rstrip("/")
        path = it.get("Url")
        if path:
            return f"{base}/{str(path).lstrip('/')}"
        return f"{base}/bostad/{_ext_id(it)}/"

    def _desc(self, it: dict[str, Any]) -> str | None:
        parts = [it.get("Kommun"), it.get("Lagenhetstyp"), it.get("KoNamn")]
        text = " · ".join(p for p in parts if p)
        return text or None
