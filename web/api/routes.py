"""Blueprint REST API: фильтры (CRUD) и профиль/удаление аккаунта.

BE-API-002 (CRUD фильтров), BE-API-006 (/me, удаление данных — GDPR).
Все эндпоинты требуют access-токен; доступ только к своим данным (BE-AU-002).
"""

from __future__ import annotations

import secrets

from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, g, jsonify, request
from pydantic import ValidationError
from shared.config import get_settings
from shared.db import COLL_FILTERS, COLL_LISTINGS, COLL_NOTIFICATIONS, COLL_USERS
from shared.models import Filter

from web.db import get_db, serialize
from web.deps import require_auth

bp = Blueprint("api", __name__, url_prefix="/api")

MAX_PAGE_LIMIT = 100
DEFAULT_PAGE_LIMIT = 20


def _oid(value: str) -> ObjectId | None:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        return None


def _pagination() -> tuple[int, int, int]:
    """(page, limit, skip) из query-параметров с безопасными границами."""
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


# --------------------------------------------------------------------------- filters


@bp.get("/filters")
@require_auth
def list_filters():
    db = get_db()
    items = [serialize(d) for d in db[COLL_FILTERS].find({"user_id": g.user_id})]
    return jsonify(items=items), 200


@bp.post("/filters")
@require_auth
def create_filter():
    data = request.get_json(silent=True) or {}
    data["user_id"] = g.user_id  # игнорируем любой user_id из тела (BE-AU-002)
    try:
        flt = Filter(**data)
    except ValidationError as exc:
        return jsonify(error="validation", detail=exc.errors(include_url=False)), 400
    res = get_db()[COLL_FILTERS].insert_one(flt.model_dump())
    return jsonify(id=str(res.inserted_id)), 201


@bp.put("/filters/<fid>")
@require_auth
def update_filter(fid: str):
    oid = _oid(fid)
    if oid is None:
        return jsonify(error="bad_id"), 400
    data = request.get_json(silent=True) or {}
    data["user_id"] = g.user_id
    try:
        flt = Filter(**data)
    except ValidationError as exc:
        return jsonify(error="validation", detail=exc.errors(include_url=False)), 400
    res = get_db()[COLL_FILTERS].update_one(
        {"_id": oid, "user_id": g.user_id}, {"$set": flt.model_dump()}
    )
    if res.matched_count == 0:
        return jsonify(error="not_found"), 404
    return jsonify(ok=True), 200


@bp.delete("/filters/<fid>")
@require_auth
def delete_filter(fid: str):
    oid = _oid(fid)
    if oid is None:
        return jsonify(error="bad_id"), 400
    res = get_db()[COLL_FILTERS].delete_one({"_id": oid, "user_id": g.user_id})
    if res.deleted_count == 0:
        return jsonify(error="not_found"), 404
    return jsonify(ok=True), 200


# --------------------------------------------------------------------------- me / GDPR


@bp.get("/me")
@require_auth
def me():
    oid = _oid(g.user_id)
    user = get_db()[COLL_USERS].find_one({"_id": oid}) if oid else None
    if not user:
        return jsonify(error="not_found"), 404
    return (
        jsonify(
            id=str(user["_id"]),
            email=user.get("email"),
            role=user.get("role", "user"),
            status=user.get("status"),
            locale=user.get("locale"),
            telegram_linked=user.get("telegram_chat_id") is not None,
        ),
        200,
    )


@bp.delete("/me")
@require_auth
def delete_me():
    """GDPR: удалить аккаунт и все связанные данные (право на удаление)."""
    db = get_db()
    oid = _oid(g.user_id)
    if oid is None:
        return jsonify(error="bad_id"), 400
    db[COLL_FILTERS].delete_many({"user_id": g.user_id})
    db[COLL_NOTIFICATIONS].delete_many({"user_id": g.user_id})
    res = db[COLL_USERS].delete_one({"_id": oid})
    if res.deleted_count == 0:
        return jsonify(error="not_found"), 404
    return jsonify(ok=True), 200


# --------------------------------------------------------------------------- listings


@bp.get("/listings")
@require_auth
def list_listings():
    """Лента объявлений (BE-API-003). `?matched=true` — только совпавшие с фильтрами пользователя.

    Доп. фильтры query: source, listing_type, district. Пагинация: page, limit.
    """
    db = get_db()
    page, limit, skip = _pagination()

    if request.args.get("matched") == "true":
        # объявления, по которым у пользователя есть уведомления (совпадения)
        raw_ids = db[COLL_NOTIFICATIONS].distinct("listing_id", {"user_id": g.user_id})
        oids = [o for o in (_oid(x) for x in raw_ids) if o is not None]
        query: dict = {"_id": {"$in": oids}}
    else:
        query = {}
        for key in ("source", "listing_type", "district"):
            val = request.args.get(key)
            if val:
                query[key] = val

    total = db[COLL_LISTINGS].count_documents(query)
    cursor = db[COLL_LISTINGS].find(query).sort("fetched_at", -1).skip(skip).limit(limit)
    items = [serialize(d) for d in cursor]
    return jsonify(items=items, page=page, limit=limit, total=total), 200


# --------------------------------------------------------------------------- notifications


@bp.get("/notifications")
@require_auth
def list_notifications():
    """История уведомлений пользователя с пагинацией (BE-API-004)."""
    db = get_db()
    page, limit, skip = _pagination()
    query = {"user_id": g.user_id}
    total = db[COLL_NOTIFICATIONS].count_documents(query)
    cursor = db[COLL_NOTIFICATIONS].find(query).sort("sent_at", -1).skip(skip).limit(limit)
    items = [serialize(d) for d in cursor]
    return jsonify(items=items, page=page, limit=limit, total=total), 200


# --------------------------------------------------------------------------- telegram


@bp.post("/telegram/link")
@require_auth
def telegram_link():
    """Сгенерировать код привязки и deep-link бота (BE-API-005, BE-NT-005).

    Бот (Фаза 3) по /start <code> свяжет telegram_chat_id с аккаунтом.
    """
    db = get_db()
    oid = _oid(g.user_id)
    if oid is None:
        return jsonify(error="bad_id"), 400
    code = secrets.token_urlsafe(8)
    db[COLL_USERS].update_one({"_id": oid}, {"$set": {"link_code": code}})
    username = get_settings().telegram_bot_username
    deep_link = f"https://t.me/{username}?start={code}" if username else None
    return jsonify(link_code=code, deep_link=deep_link), 200


@bp.get("/telegram/status")
@require_auth
def telegram_status():
    db = get_db()
    user = db[COLL_USERS].find_one({"_id": _oid(g.user_id)})
    if not user:
        return jsonify(error="not_found"), 404
    return (
        jsonify(
            linked=user.get("telegram_chat_id") is not None,
            bot_username=get_settings().telegram_bot_username or None,
        ),
        200,
    )
