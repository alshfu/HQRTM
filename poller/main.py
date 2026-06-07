"""Точка входа поллера — async-цикл опроса (Фаза 2).

Запуск: python -m poller.main

Цикл (Фаза 2): fetch (HomeQAdapter) → dedup (seen_listings) → detect FCFS →
match (фильтры) → dispatch (Telegram). С backoff и адаптивной частотой (HOT_HOURS).
"""

from __future__ import annotations

import asyncio

from shared.config import get_settings


async def run() -> None:
    settings = get_settings()
    # TODO(Фаза 2): основной цикл опроса с backoff и адаптивной частотой.
    raise NotImplementedError(f"Поллер — Фаза 2 (POLL_INTERVAL_MS={settings.poll_interval_ms})")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
