"""Små verktyg, gemensamma för processerna."""

from __future__ import annotations


def parse_hot_hours(value: str) -> tuple[int, int]:
    """Tolka fönstret med «heta» timmar av formen "08-22" till (start, end).

    Används av pollern för adaptiv pollningsfrekvens (BE-DE-004).
    Accepterar timmar 0..23, start kan vara senare än end (fönster över midnatt).
    """
    try:
        start_s, end_s = value.split("-", 1)
        start, end = int(start_s), int(end_s)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"Ogiltigt format på HOT_HOURS: {value!r}, förväntar 'HH-HH'") from exc

    for h in (start, end):
        if not 0 <= h <= 23:
            raise ValueError(f"Timme utanför intervallet 0..23: {h}")
    return start, end


def is_hot_hour(hour: int, window: tuple[int, int]) -> bool:
    """Om timmen faller inom det «heta» fönstret (med stöd för övergång över midnatt)."""
    start, end = window
    if start <= end:
        return start <= hour < end
    return hour >= start or hour < end
