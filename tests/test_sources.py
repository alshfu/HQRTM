"""Tester för registret över plattformsadaptrar (multi-source-ramverk)."""

from __future__ import annotations

from poller.sources import enabled_adapters  # import av paketet registrerar alla adaptrar
from poller.sources.registry import all_adapters
from shared.models import Source


def test_homeq_and_qasa_registered():
    sources = {cls.source for cls in all_adapters()}
    assert Source.HOMEQ in sources
    assert Source.QASA in sources


def test_adapters_disabled_until_tos_checked():
    # tills plattformarnas ToS bekräftats — ingen adapter är aktiverad (COMPLIANCE.md)
    assert enabled_adapters() == []
