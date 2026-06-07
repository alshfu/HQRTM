"""Точка входа поллера — async-цикл опроса (Фаза 2).

Запуск: python -m poller.main

Цикл: для каждого включённого адаптера → fetch → process_new_listings (дедуп/детект/upsert) →
enqueue_notifications (матчинг + queued-уведомления). Доставка в Telegram — Фаза 3.
Адаптивная частота (HOT_HOURS) + экспоненциальный backoff.
Адаптеры включаются (`enabled=True`) только после фиксации ToS (COMPLIANCE.md).
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

_NIGHT_FACTOR = 4  # ночью опрашиваем в N раз реже
_MAX_BACKOFF_MS = 60_000


def current_interval_ms(hour: int) -> int:
    """Интервал опроса для часа: базовый в «горячие» часы, реже — ночью (BE-DE-004)."""
    settings = get_settings()
    base = settings.poll_interval_ms
    window = parse_hot_hours(settings.hot_hours)
    return base if is_hot_hour(hour, window) else base * _NIGHT_FACTOR


async def run_once(db, adapters) -> list[dict]:
    """Один проход по всем адаптерам. Возвращает новые FCFS-объявления."""
    new_fcfs: list[dict] = []
    for adapter in adapters:
        try:
            raw = await adapter.fetch_listings()
        except NotImplementedError:
            continue  # адаптер ещё не реализован
        except Exception as exc:  # noqa: BLE001 — сбой источника не должен ронять цикл
            log.warning("Адаптер %s: ошибка опроса: %s", adapter.source, exc)
            continue
        for item in raw:
            item.setdefault("source", str(adapter.source))
        batch = process_new_listings(db, raw)
        enqueue_notifications(db, batch)  # матчинг + постановка уведомлений (доставка — Фаза 3)
        new_fcfs.extend(batch)
    return new_fcfs


async def run(db=None) -> None:
    if db is None:
        from shared.db import get_sync_db

        db = get_sync_db()

    adapters = enabled_adapters()
    if not adapters:
        log.warning(
            "Нет включённых адаптеров — проверьте ToS площадок (COMPLIANCE.md) и enabled=True."
        )

    backoff_ms = 0
    while True:
        try:
            await run_once(db, adapters)
            backoff_ms = 0
        except Exception as exc:  # noqa: BLE001 — устойчивость цикла (BE-RS-002)
            backoff_ms = min(_MAX_BACKOFF_MS, (backoff_ms or 1000) * 2)
            log.error("Сбой цикла поллера, backoff %d мс: %s", backoff_ms, exc)

        interval = backoff_ms or current_interval_ms(datetime.now().hour)  # noqa: DTZ005
        await asyncio.sleep(interval / 1000)


def main() -> None:
    logging.basicConfig(level=get_settings().log_level)
    asyncio.run(run())


if __name__ == "__main__":
    main()
