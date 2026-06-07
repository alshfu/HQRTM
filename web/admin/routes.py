"""Blueprint админ-API: сводная статистика и управление пользователями.

Доступ только для роли admin (`require_admin`). Префикс `/api/admin`.
Без PII в логах; смена роли не позволяет администратору разжаловать самого себя
(защита от случайной потери доступа).
"""

from __future__ import annotations

from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, g, jsonify, request
from shared.db import COLL_FILTERS, COLL_LISTINGS, COLL_NOTIFICATIONS, COLL_USERS
from shared.models import UserRole

from web.db import get_db, serialize
from web.deps import require_admin

bp = Blueprint("admin", __name__, url_prefix="/api/admin")

MAX_PAGE_LIMIT = 100
DEFAULT_PAGE_LIMIT = 20


def _oid(value: str) -> ObjectId | None:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        return None


def _pagination() -> tuple[int, int, int]:
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (TypeError, ValueError):
        page = 1
    try:
        limit = int(request.args.get("limit", DEFAULT_PAGE_LIMIT))
    except (TypeError, ValueError):
        limit = DEFAULT_PAGE_LIMIT
    limit = max(1, min(limit, MAX_PAGE_LIMIT))
    return page, limit, (page - 1) * limit


@bp.get("/stats")
@require_admin
def stats():
    """Сводные счётчики по коллекциям (для дашборда админа)."""
    db = get_db()
    return (
        jsonify(
            users=db[COLL_USERS].count_documents({}),
            filters=db[COLL_FILTERS].count_documents({}),
            listings=db[COLL_LISTINGS].count_documents({}),
            notifications=db[COLL_NOTIFICATIONS].count_documents({}),
        ),
        200,
    )


@bp.get("/users")
@require_admin
def list_users():
    """Список пользователей (без секретов), пагинация ?page=&limit=."""
    db = get_db()
    page, limit, skip = _pagination()
    total = db[COLL_USERS].count_documents({})
    cursor = (
        db[COLL_USERS]
        .find({}, {"password_hash": 0, "link_code": 0})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    items = [_public_user(serialize(d)) for d in cursor]
    return jsonify(items=items, page=page, limit=limit, total=total), 200


@bp.post("/users/<uid>/role")
@require_admin
def set_role(uid: str):
    """Сменить роль пользователя. Нельзя разжаловать самого себя (BE-AD-002)."""
    oid = _oid(uid)
    if oid is None:
        return jsonify(error="bad_id"), 400

    role = (request.get_json(silent=True) or {}).get("role")
    if role not in (UserRole.USER.value, UserRole.ADMIN.value):
        return jsonify(error="bad_role"), 400

    if uid == g.user_id and role != UserRole.ADMIN.value:
        return jsonify(error="cannot_demote_self"), 400

    res = get_db()[COLL_USERS].update_one({"_id": oid}, {"$set": {"role": role}})
    if res.matched_count == 0:
        return jsonify(error="not_found"), 404
    return jsonify(ok=True, role=role), 200


def _public_user(doc: dict | None) -> dict | None:
    """Оставить только безопасные для админ-UI поля."""
    if doc is None:
        return None
    return {
        "id": doc.get("id"),
        "email": doc.get("email"),
        "role": doc.get("role", UserRole.USER.value),
        "status": doc.get("status"),
        "telegram_linked": doc.get("telegram_chat_id") is not None,
        "created_at": doc.get("created_at"),
    }
