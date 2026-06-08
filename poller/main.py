"""Pollerns startpunkt — async-loop för bevakning (Fas 2).

Start: python -m poller.main

Loop: för varje aktiverad adapter → fetch → process_new_listings (dedup/detekt/upsert) →
enqueue_notifications (matchning + queued-aviseringar). Utskick till Telegram — Fas 3.
Adaptiv frekvens (HOT_HOURS) + exponentiell backoff.
Adaptrar aktiveras (`enabled=True`) först efter fastställd ToS (COMPLIANCE.md).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from shared.config import get_settings
from shared.utils import is_hot_hour, parse_hot_hours

from poller.engine import enqueue_notifications, process_new_listings
from poller.sources import enabled_adapters

log = logging.getLogger("hqrtm.poller")

_NIGHT_FACTOR = 4  # nattetid bevakar vi N gånger mer sällan
_MAX_BACKOFF_MS = 60_000


def current_interval_ms(hour: int) -> int:
    """Bevakningsintervall för timmen: bas under heta timmar, mer sällan nattetid (BE-DE-004)."""
    settings = get_settings()
    base = settings.poll_interval_ms
    window = parse_hot_hours(settings.hot_hours)
    return base if is_hot_hour(hour, window) else base * _NIGHT_FACTOR


async def run_once(db, adapters) -> list[dict]:
    """En genomgång av alla adaptrar. Returnerar nya FCFS-annonser."""
    new_fcfs: list[dict] = []
    fetched = 0
    queued = 0
    for adapter in adapters:
        try:
            raw = await adapter.fetch_listings()
        except NotImplementedError:
            continue  # adaptern är ännu inte implementerad
        except Exception as exc:  # noqa: BLE001 — källfel ska inte fälla loopen
            log.warning("Adapter %s: fel vid bevakning: %s", adapter.source, exc)
            continue
        for item in raw:
            item.setdefault("source", str(adapter.source))
        fetched += len(raw)
        batch = process_new_listings(db, raw)
        # matchning + kö av aviseringar (utskick — Fas 3)
        queued += enqueue_notifications(db, batch)
        new_fcfs.extend(batch)
    # Mätvärden per cykel (Fas 8): info om något nytt hände, annars debug.
    level = logging.INFO if (new_fcfs or queued) else logging.DEBUG
    log.log(level, "cykel: hämtade=%d nya_fcfs=%d aviseringar=%d", fetched, len(new_fcfs), queued)
    return new_fcfs


async def run(db=None) -> None:
    if db is None:
        from shared.db import get_sync_db

        db = get_sync_db()

    adapters = enabled_adapters()
    if not adapters:
        log.warning(
            "Inga aktiverade adaptrar — kontrollera plattformarnas ToS (COMPLIANCE.md) "
            "och enabled=True."
        )

    backoff_ms = 0
    while True:
        try:
            await run_once(db, adapters)
            backoff_ms = 0
        except Exception as exc:  # noqa: BLE001 — loopens robusthet (BE-RS-002)
            backoff_ms = min(_MAX_BACKOFF_MS, (backoff_ms or 1000) * 2)
            log.error("Fel i poller-loopen, backoff %d ms: %s", backoff_ms, exc)

        interval = backoff_ms or current_interval_ms(datetime.now().hour)  # noqa: DTZ005
        await asyncio.sleep(interval / 1000)


def main() -> None:
    from shared.logging import setup_logging

    setup_logging()
    asyncio.run(run())


if __name__ == "__main__":
    main()
