"""Blueprint REST API: фильтры (CRUD) и профиль/удаление аккаунта.

BE-API-002 (CRUD фильтров), BE-API-006 (/me, удаление данных — GDPR).
Все эндпоинты требуют access-токен; доступ только к своим данным (BE-AU-002).
"""

from __future__ import annotations

from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, g, jsonify, request
from pydantic import ValidationError
from shared.db import COLL_FILTERS, COLL_NOTIFICATIONS, COLL_USERS
from shared.models import Filter

from web.db import get_db, serialize
from web.deps import require_auth

bp = Blueprint("api", __name__, url_prefix="/api")


def _oid(value: str) -> ObjectId | None:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        return None


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
