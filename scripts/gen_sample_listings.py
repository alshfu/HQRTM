"""Generera urval av annonser från AKTIVERADE adaptrar (endast riktig data, ingen fiktion).

Kör **endast** adaptrar som är ``enabled=True`` i registret — dvs riktig data hämtad från
plattformarnas officiella API. Inga påhittade/mockade annonser publiceras någonsin.

Är ingen adapter aktiverad (de väntar på API-nyckel + bekräftad ToS, se COMPLIANCE.md) blir
urvalet **tomt** — och vitrinen visar ett ärligt tomt läge istället för fiktiva annonser.

När ägaren har skaffat t.ex. HomeQ Core API-nyckel (``HOMEQ_USERNAME``/``HOMEQ_PASSWORD``) och
satt ``enabled=True`` på adaptern hämtar detta skript riktiga annonser via samma parser som
produktionen.

Kör:  python -m scripts.gen_sample_listings
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from poller.sources import enabled_adapters

OUT = Path(__file__).resolve().parent.parent / "HQRTM-Demo" / "sample-listings.js"

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
    """Hämta annonser från alla aktiverade adaptrar (tom lista om inga är aktiverade)."""
    listings: list[dict] = []
    for adapter in enabled_adapters():
        try:
            listings += await adapter.fetch_listings()
        finally:
            close = getattr(adapter, "aclose", None)
            if close is not None:
                await close()
    return [{k: item.get(k) for k in _KEEP} for item in listings]


def main() -> None:
    listings = asyncio.run(collect())
    payload = json.dumps(listings, ensure_ascii=False, indent=2)
    banner = "// AUTO-GENERERAD av scripts/gen_sample_listings.py — REDIGERA INTE för hand.\n"
    if listings:
        banner += "// Riktig data hämtad från aktiverade källadaptrar (ingen fiktion).\n"
    else:
        banner += (
            "// Tomt: inga aktiverade adaptrar (väntar på API-nyckel + ToS, COMPLIANCE.md).\n"
            "// Inga påhittade annonser publiceras.\n"
        )
    OUT.write_text(f"{banner}window.HQRTM_SAMPLE = {payload};\n", encoding="utf-8")
    print(f"Skrev {len(listings)} annonser → {OUT}")


if __name__ == "__main__":
    main()
