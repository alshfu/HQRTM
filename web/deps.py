"""Зависимости/декораторы для эндпоинтов (аутентификация)."""

from __future__ import annotations

from functools import wraps

import jwt
from flask import g, jsonify, request
from shared.security import decode_token


def require_auth(fn):
    """Требует валидный Bearer access-токен; кладёт user_id в `g.user_id` (BE-AU-002)."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify(error="missing_token"), 401
        token = header[len("Bearer ") :]
        try:
            payload = decode_token(token, expected_type="access")
        except jwt.ExpiredSignatureError:
            return jsonify(error="token_expired"), 401
        except jwt.InvalidTokenError:
            return jsonify(error="invalid_token"), 401
        g.user_id = payload["sub"]
        return fn(*args, **kwargs)

    return wrapper
