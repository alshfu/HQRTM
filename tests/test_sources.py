"""Тесты реестра адаптеров площадок (мульти-source каркас)."""

from __future__ import annotations

from poller.sources import enabled_adapters  # импорт пакета регистрирует все адаптеры
from poller.sources.registry import all_adapters
from shared.models import Source


def test_homeq_and_qasa_registered():
    sources = {cls.source for cls in all_adapters()}
    assert Source.HOMEQ in sources
    assert Source.QASA in sources


def test_adapters_disabled_until_tos_checked():
    # пока ToS площадок не подтверждён — ни один адаптер не включён (COMPLIANCE.md)
    assert enabled_adapters() == []
