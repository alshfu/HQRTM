"""Matchning av annons mot användarnas filter (BE-FL-004, BE-FL-005).

För en ny FCFS-annons hittar vi alla användare vars aktiva filter matchar.
Logiken är synkron (pymongo/mongomock), liksom `engine` — HTTP-samtidighet i `main.py`.

Strategi: grov gallring av aktiva filter på Mongo-sidan (index `user_active` +
begränsning på `source`), sedan exakt kontroll av intervall (hyra/rum/yta) och
distrikt i Python — intervall med luckor (None) är krångliga i Mongo-frågan och svårlästa.
Antalet aktiva filter är måttligt → vi håller oss inom matchningsbudgeten (~0.05–0.15 s).
"""

from __future__ import annotations

from shared.db import COLL_FILTERS
from shared.models import ListingType


def _in_range(value, lo, hi) -> bool:
    """value ligger i [lo, hi]. Om en gräns är satt men värdet saknas — ingen match."""
    if lo is not None:
        if value is None or value < lo:
            return False
    if hi is not None:
        if value is None or value > hi:
            return False
    return True


def _district_ok(filt: dict, listing: dict) -> bool:
    """Filtrets distrikt/stad mot annonsens distrikt (case-insensitive delsträng).

    `Listing` har inget separat city-fält — adaptrarna lägger kommun/stad i `district`,
    därför jämför vi både `filter.city` och `filter.district` mot `listing.district`.
    """
    wanted = filt.get("district") or filt.get("city")
    if not wanted:
        return True
    hay = (listing.get("district") or "").lower()
    return wanted.lower() in hay


def matches(filt: dict, listing: dict) -> bool:
    """True om annonsen passar filtret."""
    # only_fcfs (default True): kö-annonser visar vi inte
    if filt.get("only_fcfs", True) and listing.get("listing_type") != ListingType.FCFS.value:
        return False

    # källor: None/tomt → alla plattformar; annars — endast de uppräknade
    sources = filt.get("sources")
    if sources and listing.get("source") not in sources:
        return False

    if not _in_range(listing.get("rent"), filt.get("rent_min"), filt.get("rent_max")):
        return False
    if not _in_range(listing.get("rooms"), filt.get("rooms_min"), filt.get("rooms_max")):
        return False
    if not _in_range(listing.get("area_m2"), filt.get("area_min"), filt.get("area_max")):
        return False

    return _district_ok(filt, listing)


def match_users(db, listing: dict) -> list[str]:
    """Returnera unika user_id för alla vars aktiva filter matchade annonsen."""
    query: dict = {"is_active": True}
    # grov gallring på källa: filter utan begränsning (sources=None) eller som
    # inkluderar plattformen
    source = listing.get("source")
    if source is not None:
        query["$or"] = [{"sources": None}, {"sources": source}]

    user_ids: list[str] = []
    seen: set[str] = set()
    for filt in db[COLL_FILTERS].find(query):
        if not matches(filt, listing):
            continue
        uid = filt.get("user_id")
        if uid and uid not in seen:
            seen.add(uid)
            user_ids.append(uid)
    return user_ids
