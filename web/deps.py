"""Зависимости/декораторы для эндпоинтов (аутентификация)."""

from __future__ import annotations

from functools import wraps

import jwt
from bson import ObjectId
from bson.errors import InvalidId
from flask import g, jsonify, request
from shared.db import COLL_USERS
from shared.models import UserRole
from shared.security import decode_token

from web.db import get_db


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


def require_admin(fn):
    """Требует аутентификацию + роль admin (проверяется по БД). Иначе 401/403."""

    @wraps(fn)
    @require_auth
    def wrapper(*args, **kwargs):
        try:
            oid = ObjectId(g.user_id)
        except (InvalidId, TypeError):
            return jsonify(error="invalid_token"), 401
        user = get_db()[COLL_USERS].find_one({"_id": oid}, {"role": 1})
        if not user or user.get("role") != UserRole.ADMIN.value:
            return jsonify(error="forbidden"), 403
        return fn(*args, **kwargs)

    return wrapper
