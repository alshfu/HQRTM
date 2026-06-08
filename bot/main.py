"""Ingångspunkt för Telegram-bot (Fas 3).

Körning: python -m bot.main
"""

from __future__ import annotations

import asyncio

from shared.config import get_settings


async def run() -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN är inte angivet (.env)")
    # TODO(Fas 3): aiogram Dispatcher + handlers, long-polling/webhook.
    raise NotImplementedError("Bot — Fas 3")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
