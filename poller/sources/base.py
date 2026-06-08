"""Basgränssnitt för plattformsadapter + gemensamma normaliseringshjälpare."""

from __future__ import annotations

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
        value = value.get("url") or value.get("src")
    if isinstance(value, str) and value:
        return value
    return None


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
