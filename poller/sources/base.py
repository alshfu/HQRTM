"""Basgränssnitt för plattformsadapter + gemensamma normaliseringshjälpare."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any

from shared.models import Source


def as_float(value: Any) -> float | None:
    """Säker konvertering till float (None vid saknat värde/fel)."""
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def as_int(value: Any) -> int | None:
    """Säker konvertering till int (None vid saknat värde/fel)."""
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def first_nonempty(obj: dict[str, Any], keys: tuple[str, ...]) -> Any:
    """Första icke-tomma värdet bland möjliga nyckelnamn (robust mot synonymer/versaler)."""
    for key in keys:
        value = obj.get(key)
        if value not in (None, ""):
            return value
    return None


# Vanliga nyckelnamn för bild-URL hos olika plattformar (best-effort).
_IMAGE_KEYS = ("image_url", "imageUrl", "image", "primary_image", "thumbnail", "cover")


def pick_image(obj: dict[str, Any]) -> str | None:
    """Plocka ut en bild-URL ur ett källobjekt: enkel nyckel, lista eller {url:...}-objekt."""
    value = first_nonempty(obj, _IMAGE_KEYS)
    # Lista av bilder → ta den första; element kan vara str eller {url|src:...}.
    images = obj.get("images")
    if value is None and isinstance(images, list) and images:
        value = images[0]
    if isinstance(value, dict):
        value = value.get("url") or value.get("src") or value.get("image")
    if isinstance(value, str) and value:
        return value
    return None


# --------------------------------------------------------------------------- feature-extraktion
#
# Plattformarnas list-API:er exponerar sällan balkong/kök/våning som strukturerade fält
# (verifierat mot HomeQ/Qasa 2026-06-10). Vi utvinner dem därför ur annonsens EGEN text
# (titel/beskrivning/adress) — riktig källdata, ingen fiktion (Beslutslogg). Hittas inget →
# fältet förblir None ("okänt"), och matcharen behandlar okänt enligt sin policy.

_BALCONY_RE = re.compile(r"\b(balkong|fransk\s+balkong|altan|uteplats|terrass|loftgång)", re.I)
_KITCHEN_RE = re.compile(r"\b(kök|kokvrå|kitchenette|pentry|trinettkök|köksö)", re.I)
# Våning: "3 tr", "vån 3", "våning 3", "3:e våningen", "plan 3"; bottenvåning/markplan → 0.
_FLOOR_RE = re.compile(
    r"(?:\bvån(?:ing(?:en)?)?\.?\s*|\bplan\s*)(\d{1,2})\b"
    r"|\b(\d{1,2})\s*(?::a|:e)?\s*(?:tr\b|trappor\b|våning)",
    re.I,
)
_GROUND_RE = re.compile(r"\b(bottenvåning|bottenplan|markplan|bv\b)", re.I)


def extract_features(*texts: str | None) -> dict[str, Any]:
    """Utvinn {has_balcony, has_kitchen, floor} ur fritext. Endast hittade nycklar returneras.

    Vi sätter bara *positiva* fynd (True / våningsnummer) — frånvaro av ett omnämnande är inte
    bevis på frånvaro, så vi sätter aldrig False/0 spekulativt (utom uttalad bottenvåning → 0).
    """
    blob = " ".join(t for t in texts if t)
    if not blob:
        return {}
    found: dict[str, Any] = {}
    if _BALCONY_RE.search(blob):
        found["has_balcony"] = True
    if _KITCHEN_RE.search(blob):
        found["has_kitchen"] = True
    floor = _parse_floor(blob)
    if floor is not None:
        found["floor"] = floor
    return found


def _parse_floor(blob: str) -> int | None:
    if _GROUND_RE.search(blob):
        return 0
    m = _FLOOR_RE.search(blob)
    if not m:
        return None
    num = m.group(1) or m.group(2)
    val = as_int(num)
    # rimlighetskontroll: våningsplan 0–60 (annars troligen ett missförstått tal, t.ex. rumsyta)
    return val if val is not None and 0 <= val <= 60 else None


class SourceAdapter(ABC):
    """Kontrakt för källadapter.

    Implementation (Fas 2): hämta plattformens data (officiellt API prioriteras,
    skrapning — fallback) och normalisera till `Listing`-dokument (som dict).
    Vid ändrad uppmärkning/kontrakt hos källan ändras ENDAST dess adapter (BE-DE-005).
    """

    #: vilken plattform (sätts i varje subklass)
    source: Source

    #: om adaptern är aktiverad som standard (avstängd tills ToS bekräftats)
    enabled: bool = False

    @abstractmethod
    async def fetch_listings(self) -> list[dict]:
        """Returnera plattformens normaliserade annonser (nycklar — `Listing`-fält)."""
        raise NotImplementedError
