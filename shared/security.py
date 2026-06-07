"""Безопасность: хэш паролей (Argon2) и JWT access/refresh (BE-AU-001, DB-004).

Секреты — из настроек (`.env`), не хардкодить. Пароли никогда не хранятся в открытом виде.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from shared.config import get_settings

_ph = PasswordHasher()
_ALG = "HS256"


# --------------------------------------------------------------------------- пароли


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False


# --------------------------------------------------------------------------- JWT


def _encode(sub: str, token_type: str, ttl: timedelta) -> str:
    now = datetime.now(UTC)
    payload = {"sub": sub, "type": token_type, "iat": now, "exp": now + ttl}
    return jwt.encode(payload, get_settings().jwt_secret, algorithm=_ALG)


def create_access_token(sub: str) -> str:
    return _encode(sub, "access", timedelta(minutes=get_settings().jwt_access_ttl_min))


def create_refresh_token(sub: str) -> str:
    return _encode(sub, "refresh", timedelta(days=get_settings().jwt_refresh_ttl_days))


def decode_token(token: str, expected_type: str | None = None) -> dict:
    """Декодировать и проверить JWT. Бросает jwt.InvalidTokenError при проблеме."""
    payload = jwt.decode(token, get_settings().jwt_secret, algorithms=[_ALG])
    if expected_type is not None and payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"ожидался тип токена {expected_type!r}")
    return payload
