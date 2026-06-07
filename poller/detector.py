"""Детекция типа объявления: FCFS («Först till kvarn») vs очередь.

Реализуется в Фазе 2 (BE-FL-001), покрывается unit-тестами на граничные случаи.
Только FCFS проходят дальше; очередные отсекаются на самом раннем этапе (BE-FL-002).
"""

from __future__ import annotations


def is_fcfs(listing: dict) -> bool:
    """True, если объявление типа FCFS. Логика — Фаза 2."""
    raise NotImplementedError("is_fcfs() — Фаза 2")
