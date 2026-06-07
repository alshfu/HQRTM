"""Матчинг объявления с фильтрами пользователей (BE-FL-004, BE-FL-005).

Для нового FCFS-объявления находим всех пользователей, чей активный фильтр совпадает.
Логика синхронная (pymongo/mongomock), как и `engine` — HTTP-конкурентность в `main.py`.

Стратегия: грубый отсев активных фильтров на стороне Mongo (индекс `user_active` +
ограничение по `source`), затем точная проверка диапазонов (цена/комнаты/площадь) и
района в Python — диапазоны с пропусками (None) фиддлятся в Mongo-запросе и хуже читаются.
Число активных фильтров умеренное → укладываемся в бюджет матчинга (~0.05–0.15 с).
"""

from __future__ import annotations

from shared.db import COLL_FILTERS
from shared.models import ListingType


def _in_range(value, lo, hi) -> bool:
    """value попадает в [lo, hi]. Если задана граница, а значения нет — не совпало."""
    if lo is not None:
        if value is None or value < lo:
            return False
    if hi is not None:
        if value is None or value > hi:
            return False
    return True


def _district_ok(filt: dict, listing: dict) -> bool:
    """Район/город фильтра против района объявления (case-insensitive подстрока).

    У `Listing` нет отдельного поля city — адаптеры кладут муниципалитет/город в `district`,
    поэтому и `filter.city`, и `filter.district` сверяем с `listing.district`.
    """
    wanted = filt.get("district") or filt.get("city")
    if not wanted:
        return True
    hay = (listing.get("district") or "").lower()
    return wanted.lower() in hay


def matches(filt: dict, listing: dict) -> bool:
    """True, если объявление подходит под фильтр."""
    # only_fcfs (по умолчанию True): очередные не показываем
    if filt.get("only_fcfs", True) and listing.get("listing_type") != ListingType.FCFS.value:
        return False

    # источники: None/пусто → все площадки; иначе — только перечисленные
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
    """Вернуть уникальные user_id всех, чьи активные фильтры совпали с объявлением."""
    query: dict = {"is_active": True}
    # грубый отсев по источнику: фильтр без ограничения (sources=None) или включающий площадку
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
