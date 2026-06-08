"""Tjänstelogik för Telegram-boten — koppling av konto + leverans av aviseringar.

Ren DB-logik utan aiogram-beroende → enhetstestbar med mongomock. ``bot/main.py`` och
``bot/handlers.py`` använder dessa funktioner för det faktiska Telegram-flödet (Fas 3).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from pymongo import ReturnDocument
from shared.db import COLL_LISTINGS, COLL_NOTIFICATIONS, COLL_USERS
from shared.models import NotificationStatus


def _oid(value: Any) -> ObjectId | None:
    try:
        return ObjectId(value)
    except Exception:  # noqa: BLE001 — ogiltigt id → None
        return None


def _now() -> datetime:
    return datetime.now(UTC)


def link_by_code(db, code: str | None, chat_id: int) -> dict | None:
    """Koppla ``telegram_chat_id`` till kontot via engångskoden. Returnerar användaren eller None.

    Koden förbrukas (``link_code`` rensas) så att den inte kan återanvändas.
    """
    if not code:
        return None
    return db[COLL_USERS].find_one_and_update(
        {"link_code": code},
        {"$set": {"telegram_chat_id": int(chat_id)}, "$unset": {"link_code": ""}},
        return_document=ReturnDocument.AFTER,
    )


def pending_notifications(db, limit: int = 20) -> list[dict]:
    """Köade aviseringar för kopplade användare, berikade med chat_id + annons."""
    out: list[dict] = []
    cursor = db[COLL_NOTIFICATIONS].find({"status": NotificationStatus.QUEUED.value}).limit(limit)
    for n in cursor:
        user = db[COLL_USERS].find_one({"_id": _oid(n["user_id"])})
        chat_id = user.get("telegram_chat_id") if user else None
        if not chat_id:
            continue  # ej kopplad → vänta (levereras när användaren kopplat Telegram)
        listing = db[COLL_LISTINGS].find_one({"_id": _oid(n["listing_id"])}) or {}
        out.append(
            {
                "notif_id": n["_id"],
                "chat_id": chat_id,
                "listing": listing,
                "locale": user.get("locale") or "sv",
            }
        )
    return out


def mark_delivered(db, notif_id, latency_ms: int | None = None) -> None:
    db[COLL_NOTIFICATIONS].update_one(
        {"_id": notif_id},
        {
            "$set": {
                "status": NotificationStatus.DELIVERED.value,
                "latency_ms": latency_ms,
                "sent_at": _now(),
            }
        },
    )


def mark_failed(db, notif_id, error: Any) -> None:
    db[COLL_NOTIFICATIONS].update_one(
        {"_id": notif_id},
        {
            "$set": {
                "status": NotificationStatus.FAILED.value,
                "error": str(error)[:200],
                "sent_at": _now(),
            }
        },
    )


def latency_ms_for(listing: dict) -> int | None:
    """Latens publish→nu i ms utifrån annonsens ``fetched_at`` (None om saknas)."""
    ts = listing.get("fetched_at")
    if not isinstance(ts, datetime):
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    return max(0, int((_now() - ts).total_seconds() * 1000))


def render_message(listing: dict, locale: str = "sv") -> str:
    """Bygg aviseringstext: FCFS-märke, titel/område, specs, länk till förstakällan."""
    sv = locale != "en"
    title = listing.get("title") or ("Bostad" if sv else "Listing")
    is_fcfs = listing.get("fcfs") or listing.get("listing_type") == "fcfs"
    head = (
        ("🔥 Först till kvarn!" if is_fcfs else "Ny annons")
        if sv
        else ("🔥 First come, first served!" if is_fcfs else "New listing")
    )
    specs: list[str] = []
    if listing.get("rooms") is not None:
        specs.append(f"{listing['rooms']:g} rum")
    if listing.get("area_m2") is not None:
        specs.append(f"{listing['area_m2']:g} m²")
    if listing.get("rent") is not None:
        specs.append(f"{listing['rent']} kr/mån")
    district = listing.get("district")
    lines = [head, "🏠 " + title + (f" · {district}" if district else "")]
    if specs:
        lines.append(" · ".join(specs))
    if listing.get("url"):
        lines.append(("👉 Ansök: " if sv else "👉 Apply: ") + listing["url"])
    return "\n".join(lines)
