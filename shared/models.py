"""Pydantic-схемы документов MongoDB (Roadmap §3).

Заглушки Фазы 0 — полная валидация и поля будут добавлены в Фазе 1.
Коллекции: users, filters, listings, notifications, seen_listings, audit_log.
"""

from __future__ import annotations

from pydantic import BaseModel


class Listing(BaseModel):
    """Нормализованное объявление HomeQ. Полная схема — Фаза 1 (BE-DE-006)."""

    external_id: str
    title: str
    url: str
    listing_type: str | None = None  # "fcfs" | "queue" | ... — детекция в Фазе 2


class Filter(BaseModel):
    """Фильтр пользователя. Полная схема — Фаза 1."""

    user_id: str
    name: str
    only_fcfs: bool = True
    is_active: bool = True
