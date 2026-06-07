"""HomeQAdapter — получение и нормализация данных HomeQ (BE-DE-001, BE-DE-005, BE-DE-006).

Изолированный адаптер: при изменении источника правится ТОЛЬКО этот файл.
API в приоритете, скрейпинг (Playwright) — fallback. Реализуется в Фазе 2,
после фиксации выводов по ToS в COMPLIANCE.md.
"""

from __future__ import annotations


class HomeQAdapter:
    """Контракт адаптера источника. Реализация — Фаза 2."""

    async def fetch_listings(self) -> list[dict]:
        """Получить и нормализовать текущие объявления в модель `listings`."""
        raise NotImplementedError("HomeQAdapter.fetch_listings() — Фаза 2")
