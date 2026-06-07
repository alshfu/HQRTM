"""Расширения Flask (инициализируются в фабрике приложения)."""

from __future__ import annotations

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Rate-limiting на чувствительных эндпоинтах (BE-AU-003). init_app — в create_app.
limiter = Limiter(key_func=get_remote_address, default_limits=[])
