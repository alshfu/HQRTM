"""Детекция типа объявления: FCFS («Först till kvarn») vs очередь (Фаза 2).

Только FCFS проходят дальше; очередные отсекаются на раннем этапе (BE-FL-001/002).
Сигналы (по приоритету):
1. Явный `listing_type` из адаптера (если источник уже различает).
2. Булев флаг `fcfs` из нормализованных данных.
3. Текстовые маркеры в title/description/labels (шведские формулировки).
"""

from __future__ import annotations

from shared.models import ListingType

# Маркеры FCFS (швед.: «первый успел — первый получил»)
_FCFS_MARKERS = (
    "först till kvarn",
    "först-till-kvarn",
    "först till hyra",
    "first come",
    "first-come",
    "fcfs",
)

# Маркеры очереди (köpoäng / kötid / förtur)
_QUEUE_MARKERS = (
    "köpoäng",
    "kötid",
    "köplats",
    "kösystem",
    "förtur",
    "poäng",
    "kö ",
)


def _text(listing: dict) -> str:
    parts = [listing.get("title"), listing.get("description")]
    labels = listing.get("labels") or listing.get("tags") or []
    if isinstance(labels, list | tuple):
        parts.extend(str(x) for x in labels)
    return " ".join(p for p in parts if p).lower()


def classify(listing: dict) -> ListingType:
    """Определить тип объявления."""
    explicit = listing.get("listing_type")
    if explicit in (ListingType.FCFS.value, ListingType.QUEUE.value):
        return ListingType(explicit)

    flag = listing.get("fcfs")
    if flag is True:
        return ListingType.FCFS
    if flag is False:
        return ListingType.QUEUE

    text = _text(listing)
    if any(m in text for m in _FCFS_MARKERS):
        return ListingType.FCFS
    if any(m in text for m in _QUEUE_MARKERS):
        return ListingType.QUEUE
    return ListingType.UNKNOWN


def is_fcfs(listing: dict) -> bool:
    """True, если объявление типа FCFS (целевое)."""
    return classify(listing) is ListingType.FCFS
