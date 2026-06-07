"""Тесты реестра адаптеров площадок (мульти-source каркас)."""

from __future__ import annotations

import poller.sources.homeq  # noqa: F401  — регистрирует HomeQAdapter
from poller.sources import enabled_adapters
from poller.sources.registry import all_adapters
from shared.models import Source


def test_homeq_registered():
    sources = {cls.source for cls in all_adapters()}
    assert Source.HOMEQ in sources


def test_adapters_disabled_until_tos_checked():
    # пока ToS площадок не подтверждён — ни один адаптер не включён (COMPLIANCE.md)
    assert enabled_adapters() == []
