"""Register över plattformsadaptrar.

Adaptrar registreras med dekoratorn @register. Pollern tar de aktiverade ur registret —
att lägga till en ny plattform kräver inga ändringar i pollerns kärna (öppen för utökning).
"""

from __future__ import annotations

from shared.models import Source

from poller.sources.base import SourceAdapter

_REGISTRY: dict[Source, type[SourceAdapter]] = {}


def register(cls: type[SourceAdapter]) -> type[SourceAdapter]:
    """Registrera en adapterklass (dekorator)."""
    if not getattr(cls, "source", None):
        raise ValueError(f"{cls.__name__}: attributet `source` är inte satt")
    _REGISTRY[cls.source] = cls
    return cls


def all_adapters() -> list[type[SourceAdapter]]:
    return list(_REGISTRY.values())


def enabled_adapters() -> list[SourceAdapter]:
    """Instanser av aktiverade adaptrar (enabled=True)."""
    return [cls() for cls in _REGISTRY.values() if cls.enabled]
