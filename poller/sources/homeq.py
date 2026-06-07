"""Адаптер HomeQ (homeq.se) — первый источник, FCFS «Först till kvarn».

Путь реализации (ресёрч 2026-06-07, см. COMPLIANCE.md): **официальный HomeQ Core API**
(`docs-core.homeq.se`, auth `/api/v2/tokens/`, Card Search опубликованных объявлений + webhooks).
Нужен API-ключ из landlord-портала. Webhooks предпочтительны для real-time FCFS.
До получения ключа/подтверждения ToS `enabled=False` — поллер его не опрашивает.

fetch_listings() должен: вызвать Card Search (или принять webhook-события), нормализовать
в поля модели Listing (source/external_id/title/url/district/rooms/area_m2/rent/listing_type).
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
