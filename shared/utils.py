"""Мелкие утилиты, общие для процессов."""

from __future__ import annotations


def parse_hot_hours(value: str) -> tuple[int, int]:
    """Разобрать окно «горячих» часов вида "08-22" в (start, end).

    Используется поллером для адаптивной частоты опроса (BE-DE-004).
    Принимает часы 0..23, start может быть позже end (окно через полночь).
    """
    try:
        start_s, end_s = value.split("-", 1)
        start, end = int(start_s), int(end_s)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"Неверный формат HOT_HOURS: {value!r}, ожидается 'HH-HH'") from exc

    for h in (start, end):
        if not 0 <= h <= 23:
            raise ValueError(f"Час вне диапазона 0..23: {h}")
    return start, end


def is_hot_hour(hour: int, window: tuple[int, int]) -> bool:
    """Попадает ли час в «горячее» окно (с поддержкой перехода через полночь)."""
    start, end = window
    if start <= end:
        return start <= hour < end
    return hour >= start or hour < end
