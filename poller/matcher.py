"""Матчинг объявления с фильтрами пользователей (BE-FL-004, BE-FL-005).

Эффективный запрос к MongoDB по индексам, без превышения бюджета латентности.
Реализуется в Фазе 3.
"""

from __future__ import annotations


async def match_users(listing: dict) -> list[str]:
    """Вернуть user_id всех, чьи активные фильтры совпали с объявлением. Фаза 3."""
    raise NotImplementedError("match_users() — Фаза 3")
