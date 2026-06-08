"""Blueprint för autentisering: registrering, inloggning, token-uppdatering (BE-API-001)."""

from __future__ import annotations

import jwt
from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError
from shared.db import COLL_USERS
from shared.models import User, UserStatus
from shared.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

from web.db import get_db
from web.extensions import limiter

bp = Blueprint("auth", __name__, url_prefix="/auth")

MIN_PASSWORD_LEN = 8


def _tokens(user_id: str) -> dict:
    return {
        "access_token": create_access_token(user_id),
        "refresh_token": create_refresh_token(user_id),
    }


@bp.post("/register")
@limiter.limit("5/minute")
def register():
    data = request.get_json(silent=True) or {}
    password = data.get("password") or ""
    if len(password) < MIN_PASSWORD_LEN:
        return jsonify(error="weak_password", detail=f"min {MIN_PASSWORD_LEN} chars"), 400
    try:
        user = User(
            email=data.get("email", ""),
            password_hash=hash_password(password),
            status=UserStatus.ACTIVE,
            consent_at=None,
        )
    except ValidationError as exc:
        return jsonify(error="validation", detail=exc.errors(include_url=False)), 400

    db = get_db()
    try:
        res = db[COLL_USERS].insert_one(user.model_dump())
    except DuplicateKeyError:
        return jsonify(error="email_taken"), 409

    user_id = str(res.inserted_id)
    return jsonify(id=user_id, **_tokens(user_id)), 201


@bp.post("/login")
@limiter.limit("10/minute")
def login():
    data = request.get_json(silent=True) or {}
    db = get_db()
    user = db[COLL_USERS].find_one({"email": data.get("email", "")})
    if not user or not verify_password(user["password_hash"], data.get("password", "")):
        return jsonify(error="invalid_credentials"), 401
    return jsonify(id=str(user["_id"]), **_tokens(str(user["_id"]))), 200


@bp.post("/refresh")
@limiter.limit("20/minute")
def refresh():
    data = request.get_json(silent=True) or {}
    token = data.get("refresh_token", "")
    try:
        payload = decode_token(token, expected_type="refresh")
    except jwt.InvalidTokenError:
        return jsonify(error="invalid_token"), 401
    return jsonify(access_token=create_access_token(payload["sub"])), 200
