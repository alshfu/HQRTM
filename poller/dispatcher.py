"""Dispatcher — kö/utskick av aviseringar (BE-NT-*).

Parallell async-utskick till matchade användare, strypning under Telegrams gränser,
retry med backoff, post i `notifications` + latency_ms (DB-005). Implementeras i Fas 3.
"""

from __future__ import annotations


async def dispatch(listing: dict, user_ids: list[str]) -> None:
    """Köa/skicka aviseringar till matchade användare. Fas 3."""
    raise NotImplementedError("dispatch() — Fas 3")
