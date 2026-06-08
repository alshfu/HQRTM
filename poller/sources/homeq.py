"""HomeQ-adapter (homeq.se) — första källan, FCFS «Först till kvarn».

Implementationsväg (research 2026-06-07, se COMPLIANCE.md): **officiellt HomeQ Core API**
(`docs-core.homeq.se`, bas `api.homeq.se`). Kontrakt:

* **Auth:** ``POST /api/v2/tokens/`` med ``{"username", "password"}`` → ``{"token": <JWT>, ...}``.
  Token skickas i headern ``Authorization: JWT <token>``; vid 401 — ny inloggning.
* **Card Search:** ``POST /api/v3/cards/`` → ``{"results": [...], "total_hits": N}``.
  Flaggorna ``first_come_first``/``queue_points`` filtrerar korttypen på API-sidan:
  för FCFS-bevakning frågar vi ``first_come_first=True, queue_points=False`` —
  kö-annonser kommer inte alls, avskiljning vid källan (BE-FL-002).
  Sortering ``publish_date.desc`` → de färskaste överst.

Nyckel/åtkomst — från landlord-portalen (``homeq.se/biz`` → settings/integration). Krävs
integrationsuppgifter i ``.env`` (``HOMEQ_USERNAME``/``HOMEQ_PASSWORD``).

⚠️ ``enabled=False`` tills ToS bekräftats och åtkomst erhållits (COMPLIANCE.md) — pollern
bevakar inte adaptern. Aktivering (``enabled=True``) — projektägarens beslut.

Vid ändrat kontrakt/uppmärkning hos källan ändras ENDAST denna fil (BE-DE-005).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from shared.config import get_settings
from shared.models import ListingType, Source

from poller.sources.base import SourceAdapter, as_float, as_int
from poller.sources.registry import register

log = logging.getLogger("hqrtm.poller.homeq")

_AUTH_PATH = "/api/v2/tokens/"
_CARDS_PATH = "/api/v3/cards/"


class HomeQAuthError(RuntimeError):
    """Kunde inte hämta/uppdatera JWT (saknad inloggning eller avslag från API)."""


@register
class HomeQAdapter(SourceAdapter):
    source = Source.HOMEQ
    enabled = False  # aktivera efter ToS-kontroll (COMPLIANCE.md) — ägarens beslut

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        """``client`` kan injiceras (tester/delad pool); annars skapas den vid behov."""
        self._client = client
        self._owns_client = client is None
        self._token: str | None = None

    # ---------------------------------------------------------------- lifecycle

    def _build_client(self) -> httpx.AsyncClient:
        s = get_settings()
        return httpx.AsyncClient(
            base_url=s.homeq_base_url,
            timeout=s.homeq_timeout_s,
            headers={"Content-Type": "application/json"},
        )

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = self._build_client()
        return self._client

    async def aclose(self) -> None:
        """Stäng den interna klienten (om vi skapade den själva)."""
        if self._client is not None and self._owns_client:
            await self._client.aclose()
            self._client = None

    # ---------------------------------------------------------------- auth

    async def _authenticate(self, client: httpx.AsyncClient) -> str:
        s = get_settings()
        if not s.homeq_username or not s.homeq_password:
            raise HomeQAuthError("HOMEQ_USERNAME/HOMEQ_PASSWORD är inte satta (.env)")
        resp = await client.post(
            _AUTH_PATH,
            json={"username": s.homeq_username, "password": s.homeq_password},
        )
        if resp.status_code != 200:
            raise HomeQAuthError(f"auth {resp.status_code}: {resp.text[:200]}")
        token = resp.json().get("token")
        if not token:
            raise HomeQAuthError("auth-svaret saknar fältet token")
        self._token = token
        return token

    async def _token_or_auth(self, client: httpx.AsyncClient) -> str:
        return self._token or await self._authenticate(client)

    # ---------------------------------------------------------------- fetch

    async def fetch_listings(self) -> list[dict]:
        """Returnera färska FCFS-kort från HomeQ, normaliserade till ``Listing``-fält."""
        client = await self._get_client()
        token = await self._token_or_auth(client)

        body = {
            "offset": 0,
            "amount": get_settings().homeq_fetch_amount,
            "sorting": "publish_date.desc",
            "first_come_first": True,  # endast «först till kvarn»
            "queue_points": False,  # kö-annonser avskiljs vid källan
        }
        resp = await self._cards(client, token, body)

        # JWT kan ha gått ut — en ny inloggning och nytt försök.
        if resp.status_code == 401:
            token = await self._authenticate(client)
            resp = await self._cards(client, token, body)

        if resp.status_code == 429 or resp.status_code >= 500:
            # Transient fel/strypning — kasta vidare, loopen gör backoff (BE-RS-002).
            retry_after = resp.headers.get("Retry-After")
            raise httpx.HTTPStatusError(
                f"HomeQ cards {resp.status_code}"
                + (f" Retry-After={retry_after}" if retry_after else ""),
                request=resp.request,
                response=resp,
            )
        resp.raise_for_status()

        results = resp.json().get("results", [])
        return [self._normalize(card) for card in results if card.get("id") is not None]

    async def _cards(self, client: httpx.AsyncClient, token: str, body: dict) -> httpx.Response:
        return await client.post(_CARDS_PATH, json=body, headers={"Authorization": f"JWT {token}"})

    # ---------------------------------------------------------------- normalize

    def _normalize(self, card: dict[str, Any]) -> dict:
        """HomeQ-kort → dict med fält från modellen ``Listing`` (+ ``fcfs`` för detektorn)."""
        ext_id = str(card["id"])
        return {
            "source": str(self.source),
            "external_id": ext_id,
            "title": card.get("title") or "Bostad",
            "url": self._listing_url(card, ext_id),
            "district": card.get("municipality") or card.get("city"),
            "rooms": as_float(card.get("rooms")),
            "area_m2": as_float(card.get("area")),
            "rent": as_int(card.get("rent")),
            # Förfrågan med first_come_first=True/queue_points=False → endast FCFS kom.
            "listing_type": ListingType.FCFS.value,
            "fcfs": True,
        }

    def _listing_url(self, card: dict, ext_id: str) -> str:
        uri = card.get("uri")
        base = get_settings().homeq_public_base.rstrip("/")
        if uri:
            if uri.startswith(("http://", "https://")):
                return uri
            return f"{base}/{str(uri).lstrip('/')}"
        return f"{base}/listing/{ext_id}"
