"""Detektering av annonstyp: FCFS («Först till kvarn») vs kö (Fas 2).

Endast FCFS går vidare; kö-annonser avskiljs i ett tidigt skede (BE-FL-001/002).
Signaler (efter prioritet):
1. Explicit `listing_type` från adaptern (om källan redan skiljer dem åt).
2. Boolesk flagga `fcfs` från normaliserade data.
3. Textmarkörer i title/description/labels (svenska formuleringar).
"""

from __future__ import annotations

from shared.models import ListingType

# FCFS-markörer (sv.: «först till kvarn — först till hyra»)
_FCFS_MARKERS = (
    "först till kvarn",
    "först-till-kvarn",
    "först till hyra",
    "first come",
    "first-come",
    "fcfs",
)

# Kö-markörer (köpoäng / kötid / förtur)
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
    """Bestäm annonstypen."""
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
    """True om annonsen är av typen FCFS (mål-typen)."""
    return classify(listing) is ListingType.FCFS
