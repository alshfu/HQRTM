"""Telegram-bot-handlers (aiogram): kontokoppling via deep-link/kod (Fas 3, BE-NT-005).

``build_router(db)`` returnerar en Router bunden till databasen. Kopplingslogiken ligger i
``bot.service`` (testas separat utan aiogram).
"""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message

from bot.service import link_by_code


def build_router(db) -> Router:
    """Skapa en Router vars handlers kopplar konton mot ``db``."""
    router = Router()

    @router.message(CommandStart(deep_link=True))
    async def on_deeplink(message: Message, command: CommandObject) -> None:
        user = link_by_code(db, command.args, message.chat.id)
        if user:
            await message.answer("✅ Kopplat! Du får nu aviseringar om matchande bostäder här.")
        else:
            await message.answer("Ogiltig eller använd kod. Skapa en ny: appen → Konto → Telegram.")

    @router.message(CommandStart())
    async def on_start(message: Message) -> None:
        await message.answer("Hej! Koppla ditt HQRTM-konto via knappen i appen (Konto → Telegram).")

    return router
