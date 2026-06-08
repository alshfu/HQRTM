"""Ingångspunkt för Telegram-boten (Fas 3) — long-polling + leverans av aviseringar.

Körning: python -m bot.main   (kräver TELEGRAM_BOT_TOKEN i .env)

Boten kopplar konton via deep-link (/start <kod>) och levererar köade aviseringar
(status=queued) till respektive telegram_chat_id, sätter latency_ms och status=delivered.
"""

from __future__ import annotations

import asyncio
import logging

from shared.config import get_settings

log = logging.getLogger("hqrtm.bot")

_DELIVER_INTERVAL_S = 2.0


async def _deliver_loop(bot, db) -> None:
    """Pollar köade aviseringar och skickar dem till Telegram (Fas 3, BE-NT-001..003)."""
    from bot.service import (
        latency_ms_for,
        mark_delivered,
        mark_failed,
        pending_notifications,
        render_message,
    )

    while True:
        for item in pending_notifications(db):
            try:
                await bot.send_message(
                    item["chat_id"], render_message(item["listing"], item["locale"])
                )
                mark_delivered(db, item["notif_id"], latency_ms_for(item["listing"]))
            except Exception as exc:  # noqa: BLE001 — en miss ska inte fälla loopen
                log.warning("Leverans misslyckades: %s", exc)
                mark_failed(db, item["notif_id"], exc)
        await asyncio.sleep(_DELIVER_INTERVAL_S)


async def run(db=None) -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN är inte angivet (.env)")

    if db is None:
        from shared.db import ensure_indexes, get_sync_db

        db = get_sync_db()
        ensure_indexes(db)

    from aiogram import Bot, Dispatcher

    from bot.handlers import build_router

    bot = Bot(settings.telegram_bot_token)
    dp = Dispatcher()
    dp.include_router(build_router(db))

    asyncio.create_task(_deliver_loop(bot, db))
    log.info("Boten startar (long-polling)…")
    await dp.start_polling(bot)


def main() -> None:
    from shared.logging import setup_logging

    setup_logging()
    asyncio.run(run())


if __name__ == "__main__":
    main()
