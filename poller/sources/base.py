"""Базовый интерфейс адаптера площадки."""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.models import Source


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
