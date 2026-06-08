"""Generera vitrinens urval med RIKTIGA annonser från HomeQ:s publika Card Search.

Hämtar den inloggningsfria (anonyma) sökningen på ``api.homeq.se/api/v3/cards/`` — exakt samma
data som visas för besökare på ``homeq.se/search`` — och filtrerar till **Göteborgs**
storstadsområde (bbox från söklänken). Normaliseringen görs av den riktiga parsern
(``HomeQAdapter.fetch_public_cards`` → ``_normalize``). **Ingen påhittad data.** Bild + beskrivning
+ länk till förstakällan följer med.

⚠️ Detta är en explicit, ägar-godkänd engångshämtning av **publik** data (inte 24/7-polling;
adaptern förblir ``enabled=False``). Respektera plattformens ToS (COMPLIANCE.md).

Kör:  python -m scripts.gen_sample_listings
"""

from __future__ import annotations

import asyncio
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import httpx
from poller.sources.homeq import HomeQAdapter
from shared.config import get_settings

OUT = Path(__file__).resolve().parent.parent / "HQRTM-Demo" / "sample-listings.js"

# Göteborgs storstadsområde — bbox (min_lat, max_lat, min_lng, max_lng) från söklänken.
GOTEBORG_BBOX = (57.30501310262437, 57.951573625160904, 11.299629385756305, 12.662900614241892)
LIMIT = 12

# Fält som vitrinen visar (interna flaggor som fcfs städas bort).
_KEEP = (
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


async def collect() -> list[dict]:
    client = httpx.AsyncClient(
        base_url=get_settings().homeq_base_url,
        timeout=20.0,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
    )
    adapter = HomeQAdapter(client=client)
    try:
        listings = await adapter.fetch_public_cards(bbox=GOTEBORG_BBOX, limit=LIMIT)
    finally:
        await adapter.aclose()
    return [{k: item.get(k) for k in _KEEP} for item in listings]


def main() -> None:
    listings = asyncio.run(collect())
    now = datetime.now(UTC)
    meta = {
        "count": len(listings),
        "region": "Göteborg",
        "sources": dict(Counter(item.get("source") for item in listings)),
        "generatedAt": now.isoformat(timespec="seconds"),
        "clock": now.strftime("%H:%M:%S"),
    }
    payload = json.dumps(listings, ensure_ascii=False, indent=2)
    banner = (
        "// AUTO-GENERERAD av scripts/gen_sample_listings.py — REDIGERA INTE för hand.\n"
        "// Riktiga annonser från HomeQ:s publika Card Search (Göteborg). Ingen fiktion.\n"
    )
    body = (
        f"{banner}window.HQRTM_SAMPLE = {payload};\n"
        f"window.HQRTM_META = {json.dumps(meta, ensure_ascii=False)};\n"
    )
    OUT.write_text(body, encoding="utf-8")
    print(f"Skrev {len(listings)} annonser → {OUT}")


if __name__ == "__main__":
    main()
