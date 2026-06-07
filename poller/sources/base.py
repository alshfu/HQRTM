"""Базовый интерфейс адаптера площадки + общие хелперы нормализации."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from shared.models import Source


def as_float(value: Any) -> float | None:
    """Безопасное приведение к float (None при пропуске/ошибке)."""
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def as_int(value: Any) -> int | None:
    """Безопасное приведение к int (None при пропуске/ошибке)."""
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


class SourceAdapter(ABC):
    """Контракт адаптера источника.

    Реализация (Фаза 2): получить данные площадки (официальное API в приоритете,
    скрейпинг — fallback) и нормализовать в документы `Listing` (как dict).
    При изменении разметки/контракта источника правится ТОЛЬКО его адаптер (BE-DE-005).
    """

    #: какая площадка (проставляется в каждом подклассе)
    source: Source

    #: включён ли адаптер по умолчанию (выключаем, пока не подтверждён ToS)
    enabled: bool = False

    @abstractmethod
    async def fetch_listings(self) -> list[dict]:
        """Вернуть нормализованные объявления площадки (ключи — поля `Listing`)."""
        raise NotImplementedError
