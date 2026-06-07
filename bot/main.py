"""Точка входа Telegram-бота (Фаза 3).

Запуск: python -m bot.main
"""

from __future__ import annotations

import asyncio

from shared.config import get_settings


async def run() -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не задан (.env)")
    # TODO(Фаза 3): aiogram Dispatcher + handlers, long-polling/webhook.
    raise NotImplementedError("Бот — Фаза 3")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
