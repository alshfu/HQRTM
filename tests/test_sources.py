"""Tester för registret över plattformsadaptrar (multi-source-ramverk)."""

from __future__ import annotations

from poller.sources import enabled_adapters  # import av paketet registrerar alla adaptrar
from poller.sources.registry import all_adapters
from shared.models import Source


def test_sources_registered():
    sources = {cls.source for cls in all_adapters()}
    assert {Source.HOMEQ, Source.QASA, Source.SAMTRYGG, Source.BOSTADSFORMEDLINGEN} <= sources


def test_enabled_adapters_reflect_legitimacy():
    # Endast källor med legitim åtkomst är aktiverade. Bostadsförmedlingen (kommunalt öppet data)
    # är på; HomeQ/Qasa/Samtrygg är av tills ToS/nyckel bekräftats (COMPLIANCE.md).
    enabled = {a.source for a in enabled_adapters()}
    assert Source.BOSTADSFORMEDLINGEN in enabled
    assert Source.QASA not in enabled
    assert Source.SAMTRYGG not in enabled
