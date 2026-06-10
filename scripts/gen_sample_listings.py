"""Generera vitrinens urval med RIKTIGA annonser (Göteborg) från publika sökningar.

Aggregerar två inloggningsfria, publika källor för **Göteborg**:
* **HomeQ** Card Search (``api.homeq.se/api/v3/cards/``, bbox från söklänken) — FCFS.
* **Qasa** marketplace (``api.qasa.com/graphql``, ``areaIdentifier=se/goteborg``) — rik fritext,
  varifrån parsern utvinner **balkong/kök/våning** (``extract_features``).

Normaliseringen görs av de riktiga adaptrarna (``_normalize`` + ``extract_features``).
**Ingen påhittad data.** Bild + beskrivning + balkong/kök/våning + källänk följer med.

⚠️ Explicit, ägar-godkänd hämtning av **publik** data (inte 24/7-polling; HomeQ-adaptern förblir
``enabled=False``). Respektera plattformarnas ToS (COMPLIANCE.md).

Kör:  python -m scripts.gen_sample_listings
"""

from __future__ import annotations

import asyncio
import json
import os
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import httpx

# Begränsa Qasa till Göteborg innan inställningarna läses/cachas.
os.environ.setdefault("QASA_AREAS", "se/goteborg")

from poller.sources.homeq import HomeQAdapter  # noqa: E402
from poller.sources.qasa import QasaAdapter  # noqa: E402
from shared.config import get_settings  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "HQRTM-Demo" / "sample-listings.js"

# Göteborgs storstadsområde — bbox (min_lat, max_lat, min_lng, max_lng) från söklänken.
GOTEBORG_BBOX = (57.30501310262437, 57.951573625160904, 11.299629385756305, 12.662900614241892)
HOMEQ_LIMIT = 7
QASA_LIMIT = 7  # Qasa-annonser har rik fritext → balkong/kök/våning syns i vitrinen

_FEATURE_KEYS = ("floor", "has_balcony", "has_kitchen")

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
    "floor",
    "has_balcony",
    "has_kitchen",
    "listing_type",
)


async def collect() -> list[dict]:
    get_settings.cache_clear()  # plocka upp QASA_AREAS satt ovan
    out: list[dict] = []

    client = httpx.AsyncClient(
        base_url=get_settings().homeq_base_url,
        timeout=20.0,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
    )
    homeq = HomeQAdapter(client=client)
    try:
        out += await homeq.fetch_public_cards(bbox=GOTEBORG_BBOX, limit=HOMEQ_LIMIT)
    finally:
        await homeq.aclose()

    qasa = QasaAdapter()
    try:
        qasa_items = await qasa.fetch_listings()
    finally:
        await qasa.aclose()
    # Föredra annonser där minst en bekvämlighet utvunnits → vitrinen visar fälten.
    qasa_items.sort(key=lambda i: any(i.get(k) is not None for k in _FEATURE_KEYS), reverse=True)
    out += qasa_items[:QASA_LIMIT]

    return [{k: item.get(k) for k in _KEEP} for item in out]


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
        "// Riktiga annonser från HomeQ + Qasa publika sökningar (Göteborg). Ingen fiktion.\n"
    )
    body = (
        f"{banner}window.HQRTM_SAMPLE = {payload};\n"
        f"window.HQRTM_META = {json.dumps(meta, ensure_ascii=False)};\n"
    )
    OUT.write_text(body, encoding="utf-8")
    print(f"Skrev {len(listings)} annonser → {OUT}")


if __name__ == "__main__":
    main()
