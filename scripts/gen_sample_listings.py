"""Generera ett urval av annonser via den RIKTIGA parsern (för demo/vitrinen).

Kör de verkliga adaptrarna (HomeQ / Qasa / Samtrygg) mot representativa svar-fixturer med
``httpx.MockTransport`` — alltså **ingen riktig skrapning** av plattformarna (ToS respekteras,
adaptrarna är ``enabled=False``). Resultatet är normaliserat av samma kod som i produktion, så
fälten (titel, hyra, rum, yta) och **länken till källan** (``url``) kommer från parsern, inte
från handskriven mock.

Utdata: ``HQRTM-Demo/sample-listings.js`` med ``window.HQRTM_SAMPLE`` som vitrinen renderar.

Kör:  python -m scripts.gen_sample_listings
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx
from poller.sources.homeq import HomeQAdapter
from poller.sources.qasa import QasaAdapter
from poller.sources.samtrygg import SamtryggAdapter
from shared.config import get_settings

OUT = Path(__file__).resolve().parent.parent / "HQRTM-Demo" / "sample-listings.js"

# --- Representativa svar (svenskt innehåll, illustrativt — formen matchar respektive API) ---

HOMEQ_CARDS = [
    {
        "id": 184223,
        "title": "Ljus 3:a på Södermalm",
        "uri": "listing/184223",
        "municipality": "Stockholm",
        "rooms": 3,
        "area": 72,
        "rent": 14800,
        "image": "https://picsum.photos/seed/homeq-soder/640/420",
        "description": "Ljus trea med balkong, nära Mariatorget och tunnelbana.",
    },
    {
        "id": 184556,
        "title": "Nyrenoverad 2:a nära Slottsskogen",
        "uri": "listing/184556",
        "municipality": "Göteborg",
        "rooms": 2,
        "area": 56,
        "rent": 11200,
        "image": "https://picsum.photos/seed/homeq-goteborg/640/420",
        "description": "Nyrenoverad tvåa med öppen planlösning, gångavstånd till Slottsskogen.",
    },
]

QASA_NODES = [
    {
        "id": "home-90412",
        "slug": "vasastan-1a",
        "rent": 9900,
        "roomCount": 1,
        "squareMeters": 38,
        "firstHand": True,
        "displayImage": "https://picsum.photos/seed/qasa-vasastan/640/420",
        "description": "Charmig etta i Vasastan, fullt möblerad, andrahand.",
        "location": {"locality": "Stockholm", "route": "Dalagatan", "streetNumber": "21"},
    },
    {
        "id": "home-90871",
        "slug": "mollevangen-4a",
        "rent": 13500,
        "roomCount": 4,
        "squareMeters": 95,
        "firstHand": True,
        "displayImage": "https://picsum.photos/seed/qasa-malmo/640/420",
        "description": "Rymlig fyra i Möllevången, perfekt för delat boende.",
        "location": {"locality": "Malmö", "route": "Bergsgatan", "streetNumber": "9"},
    },
]

SAMTRYGG_BODY = [
    {
        "cityName": "Uppsala",
        "vacantAccomadationCount": 1,
        "RentalObjectInfo": [
            {
                "address": "Kungsgatan 54, 2 rok",
                "price": "10 300 kr/mån",
                "sqareMeters": "61 m²",
                "rentalObjectLink": "https://samtrygg.se/hyresobjekt/55012",
                "imageUrl": "https://picsum.photos/seed/samtrygg-uppsala/640/420",
                "description": "Trygg andrahandsuthyrning centralt i Uppsala.",
            }
        ],
    },
    {
        "cityName": "Lund",
        "vacantAccomadationCount": 1,
        "RentalObjectInfo": [
            {
                "address": "Clemenstorget 3, 1 rok",
                "price": "8 450 kr/mån",
                "sqareMeters": "33 m²",
                "rentalObjectLink": "https://samtrygg.se/hyresobjekt/55198",
                "imageUrl": "https://picsum.photos/seed/samtrygg-lund/640/420",
                "description": "Mysig etta vid Clemenstorget, nära universitetet.",
            }
        ],
    },
]


def _homeq_handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path.endswith("/api/v2/tokens/"):
        return httpx.Response(200, json={"token": "demo-jwt"})
    if path.endswith("/api/v3/cards/"):
        return httpx.Response(200, json={"results": HOMEQ_CARDS, "total_hits": len(HOMEQ_CARDS)})
    return httpx.Response(404, json={})


def _qasa_handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"data": {"homes": {"nodes": QASA_NODES}}})


def _samtrygg_handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json=SAMTRYGG_BODY)


async def collect() -> list[dict]:
    s = get_settings()
    # Lös upp de inställningar som adaptrarna kräver (utan riktiga hemligheter/host).
    s.homeq_username = "demo"
    s.homeq_password = "demo"  # pragma: allowlist secret  (dummy, mockad transport)
    s.samtrygg_api_url = "https://mock.local/GetHomePageObjects"

    listings: list[dict] = []

    homeq = HomeQAdapter(
        client=httpx.AsyncClient(
            transport=httpx.MockTransport(_homeq_handler), base_url=s.homeq_base_url
        )
    )
    listings += await homeq.fetch_listings()
    await homeq.aclose()

    qasa = QasaAdapter(client=httpx.AsyncClient(transport=httpx.MockTransport(_qasa_handler)))
    listings += await qasa.fetch_listings()
    await qasa.aclose()

    samtrygg = SamtryggAdapter(
        client=httpx.AsyncClient(transport=httpx.MockTransport(_samtrygg_handler))
    )
    listings += await samtrygg.fetch_listings()
    await samtrygg.aclose()

    # Behåll bara fält som vitrinen visar (städa bort interna flaggor).
    keep = (
        "source",
        "title",
        "url",
        "image_url",
        "description",
        "district",
        "rooms",
        "area_m2",
        "rent",
        "listing_type",
    )
    return [{k: item.get(k) for k in keep} for item in listings]


def main() -> None:
    listings = asyncio.run(collect())
    payload = json.dumps(listings, ensure_ascii=False, indent=2)
    banner = (
        "// AUTO-GENERERAD av scripts/gen_sample_listings.py — REDIGERA INTE för hand.\n"
        "// Urval normaliserat av den riktiga parsern (fixturer, ingen live-skrapning).\n"
    )
    OUT.write_text(f"{banner}window.HQRTM_SAMPLE = {payload};\n", encoding="utf-8")
    print(f"Skrev {len(listings)} annonser → {OUT}")


if __name__ == "__main__":
    main()
