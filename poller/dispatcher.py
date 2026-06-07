"""Dispatcher — постановка/отправка уведомлений (BE-NT-*).

Параллельная async-рассылка совпавшим пользователям, троттлинг под лимиты Telegram,
retry с backoff, запись в `notifications` + latency_ms (DB-005). Реализуется в Фазе 3.
"""

from __future__ import annotations


async def dispatch(listing: dict, user_ids: list[str]) -> None:
    """Поставить/отправить уведомления для совпавших пользователей. Фаза 3."""
    raise NotImplementedError("dispatch() — Фаза 3")
