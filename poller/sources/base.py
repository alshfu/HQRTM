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
