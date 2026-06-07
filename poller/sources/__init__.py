"""Адаптеры площадок-источников (all-in-one агрегатор).

Каждая шведская площадка жилья — отдельный адаптер `SourceAdapter`, изолирующий
получение и нормализацию данных (BE-DE-005). Поллер обходит все включённые адаптеры
из реестра и нормализует объявления в единую модель `shared.models.Listing`.

⚠️ Перед включением адаптера в проде — проверить ToS/robots.txt площадки (COMPLIANCE.md).
"""

from poller.sources.base import SourceAdapter
from poller.sources.registry import enabled_adapters, register

__all__ = ["SourceAdapter", "register", "enabled_adapters"]
