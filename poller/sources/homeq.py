"""Адаптер HomeQ (homeq.se) — первый источник, FCFS «Först till kvarn».

Реализуется в Фазе 2 после фиксации выводов по ToS HomeQ в COMPLIANCE.md.
До этого `enabled=False` — поллер его не опрашивает.
"""

from __future__ import annotations

from shared.models import Source

from poller.sources.base import SourceAdapter
from poller.sources.registry import register


@register
class HomeQAdapter(SourceAdapter):
    source = Source.HOMEQ
    enabled = False  # включить после проверки ToS (COMPLIANCE.md) — Фаза 2

    async def fetch_listings(self) -> list[dict]:
        raise NotImplementedError("HomeQAdapter.fetch_listings() — Фаза 2")
