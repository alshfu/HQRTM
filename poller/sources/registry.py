"""Реестр адаптеров площадок.

Адаптеры регистрируются декоратором @register. Поллер берёт включённые из реестра —
добавление новой площадки не требует правок в ядре поллера (открыт на расширение).
"""

from __future__ import annotations

from shared.models import Source

from poller.sources.base import SourceAdapter

_REGISTRY: dict[Source, type[SourceAdapter]] = {}


def register(cls: type[SourceAdapter]) -> type[SourceAdapter]:
    """Зарегистрировать класс-адаптер (декоратор)."""
    if not getattr(cls, "source", None):
        raise ValueError(f"{cls.__name__}: не задан атрибут `source`")
    _REGISTRY[cls.source] = cls
    return cls


def all_adapters() -> list[type[SourceAdapter]]:
    return list(_REGISTRY.values())


def enabled_adapters() -> list[SourceAdapter]:
    """Экземпляры включённых адаптеров (enabled=True)."""
    return [cls() for cls in _REGISTRY.values() if cls.enabled]
