"""Samtrygg-adapter (samtrygg.se) — «trygg» andrahandsuthyrning (uthyrning via ansökan).

Kontrakt — publik SwaggerHub-spec `Samtryg/Samtrygg/1.0.0`:
`GET /GetHomePageObjects` → en array av objekt grupperade per stad
(`RentalPropertyInfo`: `cityName`, `vacantAccomadationCount` + nästlad lista
`RentalObjectInfo`). Objektfält: `address`, `price`, `sqareMeters` (så i API — med felstavning),
`startDate`, `endDate`, `imageUrl`, `rentalObjectLink`.

⚠️ I specen är **host inte angiven** och fälten `id`/`rooms`/`title` saknas. Därför:
- ``enabled=False`` — host och åtkomstvillkor/ToS är inte bekräftade; aktivering — hos ägaren
  (se COMPLIANCE.md). Innan aktivering: fastställ bas-URL (`SAMTRYGG_API_URL`) och ToS.
- `external_id` härleds från `rentalObjectLink` (eller `address`) — stabilt id saknas i svaret.
- Den nästlade nyckeln med objektlistan heter `RentalObjectInfo` i specen, men gemener/versaler
  och namn är inte garanterade → vi parsar **defensivt** (kända nycklar, sedan heuristik: list-fält
  vars element liknar ett objekt). Vid avvikelse mot schemat ändras ENDAST denna fil (BE-DE-005).

Samtrygg — uthyrning via ansökan (ingen kö/köpoäng) → annonserna märks som FCFS.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx
from shared.config import get_settings
from shared.models import ListingType, Source

from poller.sources.base import SourceAdapter, extract_features, pick_image
from poller.sources.registry import register

log = logging.getLogger("hqrtm.poller.samtrygg")

_NUM_RE = re.compile(r"\d+(?:[.,]\d+)?")
# «2 rum», «2 rok», «3 r o k», «1,5 rum» — antal rum i fritext i adress/titel.
_ROOMS_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:r\.?o\.?k\.?|rum\b|rok\b|rms?\b)", re.IGNORECASE)

# Kända fältnamn enligt specen (+ möjliga varianter av gemener/versaler/synonymer) för robusthet.
_LINK_KEYS = ("rentalObjectLink", "RentalObjectLink", "link", "url")
_ADDRESS_KEYS = ("address", "Address", "streetAddress")
_AREA_KEYS = ("sqareMeters", "squareMeters", "sqareMeter", "area", "size")
_PRICE_KEYS = ("price", "Price", "rent", "monthlyRent")
_NESTED_LIST_KEYS = ("RentalObjectInfo", "rentalObjectInfo", "rentalObjects", "objects")


@register
class SamtryggAdapter(SourceAdapter):
    source = Source.SAMTRYGG
    enabled = False  # host/ToS ej bekräftade — aktivering hos ägaren (COMPLIANCE.md)

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
        """Returnera normaliserade Samtrygg-annonser (nycklar — ``Listing``-fält)."""
        s = get_settings()
        if not s.samtrygg_api_url:
            # Utan bekräftad host finns inget att bevaka — hoppa tyst över (adaptern är ändå
            # enabled=False; skydd ifall den aktiveras manuellt utan URL-konfiguration).
            log.debug("samtrygg: SAMTRYGG_API_URL är inte satt — hoppar över bevakningen")
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
        """Samtrygg-objekt → dict med ``Listing``-fält (+ ``fcfs`` för detektorn)."""
        link = _first(obj, _LINK_KEYS)
        address = _first(obj, _ADDRESS_KEYS)
        ext_id = link or address
        if not ext_id:
            return None  # utan stabil nyckel är dedup omöjlig — hoppa över

        title = self._title(address, city_name)
        description = _first(obj, ("description", "Description", "info"))
        doc = {
            "source": str(self.source),
            "external_id": str(ext_id),
            "title": title,
            "url": str(link or get_settings().samtrygg_public_base),
            "image_url": pick_image(obj),
            "description": description,
            "address": address,
            "district": city_name,
            "rooms": _rooms(address, title),
            "area_m2": _num(_first(obj, _AREA_KEYS), float),
            "rent": _num(_first(obj, _PRICE_KEYS), int),
            "listing_type": ListingType.FCFS.value,  # uthyrning via ansökan, inte kö
            "fcfs": True,
        }
        doc.update(extract_features(title, description, address))  # balkong/kök/våning ur texten
        return doc

    def _title(self, address: str | None, city_name: str | None) -> str:
        first = address.split(",")[0].strip() if address else None
        parts = [p for p in (first, city_name) if p]
        return ", ".join(parts) if parts else "Bostad"


def _first(obj: dict[str, Any], keys: tuple[str, ...]) -> Any:
    """Första icke-tomma värdet bland möjliga nyckelnamn (robust mot gemener/versaler/synonymer)."""
    for key in keys:
        value = obj.get(key)
        if value not in (None, ""):
            return value
    return None


def _iter_objects(payload: Any):
    """Gå defensivt igenom svaret `GetHomePageObjects` → par (cityName, objekt).

    Struktur: en topplista av «städer», i varje — `cityName` och en nästlad lista av objekt
    (`RentalObjectInfo` enligt specen). Vi tar känd nyckel, annars — första list-fältet vars
    element liknar ett objekt (har `address`/`price`/`rentalObjectLink`). Även ett
    «platt» svar stöds — en lista av själva objekten utan gruppering per stad.
    """
    groups = payload if isinstance(payload, list) else _coerce_list(payload)
    for group in groups:
        if not isinstance(group, dict):
            continue
        # Platt objektlista (utan stads-omslag): elementet självt är en annons.
        if any(k in group for k in _LINK_KEYS + _ADDRESS_KEYS) and not _has_object_list(group):
            yield None, group
            continue

        city = group.get("cityName") or group.get("city")
        for obj in _nested_objects(group):
            yield city, obj


def _coerce_list(payload: Any) -> list:
    """Plocka ut listan av grupper ur omslagsobjektet (`results`/`data`/första list-fältet)."""
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
    """Returnera nästlad objektlista: känd nyckel → annars första passande list-fältet."""
    for key in _NESTED_LIST_KEYS:
        if _looks_like_objects(group.get(key)):
            return [o for o in group[key] if isinstance(o, dict)]
    for value in group.values():
        if _looks_like_objects(value):
            return [o for o in value if isinstance(o, dict)]
    return []


def _looks_like_objects(value: Any) -> bool:
    """list är icke-tom, första elementet — dict med kännetecken för en annons."""
    return (
        isinstance(value, list)
        and bool(value)
        and isinstance(value[0], dict)
        and any(k in value[0] for k in _LINK_KEYS + _ADDRESS_KEYS + _PRICE_KEYS)
    )


def _rooms(*texts: str | None) -> float | None:
    """Extrahera antal rum ur adress/titel («2 rum», «3 rok», «1,5 rok») — None om saknas."""
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
    """Extrahera ett tal ur en sträng som '8 500 kr/mån' / '45 m²' (None om saknas)."""
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
