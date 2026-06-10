"""SSE-endpoint /sse/feed (Fas 6).

EventSource kan inte skicka headers → access-token tas emot i query `?token=`.
Strömmen text/event-stream: vid anslutning skickas `retry`+comment, sedan händelser från brokern
och heartbeat-kommentarer (upptäcker avbrott + håller anslutningen vid liv genom proxy).
"""

from __future__ import annotations

import json
import queue

import jwt
from flask import Blueprint, Response, current_app, jsonify, request
from shared.security import decode_token

from web.auth.cookies import ACCESS_COOKIE
from web.sse.broker import broker

bp = Blueprint("sse", __name__, url_prefix="/sse")

_HEARTBEAT_SEC = 15


def _user_from_request() -> str | None:
    # Token från query (EventSource kan inte sätta headers), Bearer-header eller httpOnly-cookie.
    token = request.args.get("token", "")
    if not token:
        header = request.headers.get("Authorization", "")
        if header.startswith("Bearer "):
            token = header[len("Bearer ") :]
    if not token:
        token = request.cookies.get(ACCESS_COOKIE, "")
    if not token:
        return None
    try:
        return decode_token(token, expected_type="access")["sub"]
    except jwt.InvalidTokenError:
        return None


@bp.get("/feed")
def feed():
    user_id = _user_from_request()
    if not user_id:
        return jsonify(error="invalid_token"), 401

    testing = current_app.testing
    if not testing:
        from web.sse.watcher import ensure_watcher_started

        ensure_watcher_started(current_app.config["DB"])

    q = broker.subscribe(user_id)

    def stream():
        # föreslår klienten ett återanslutningsintervall och bekräftar anslutningen
        yield "retry: 3000\n\n"
        yield ": connected\n\n"
        try:
            if testing:
                # i tester blockerar vi inte: skickar de samlade händelserna och avslutar
                while True:
                    try:
                        data = q.get_nowait()
                    except queue.Empty:
                        break
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                return
            while True:
                try:
                    data = q.get(timeout=_HEARTBEAT_SEC)
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                except queue.Empty:
                    yield ": keepalive\n\n"
        finally:
            broker.unsubscribe(user_id, q)

    return Response(
        stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # inaktivera buffring i Nginx
            "Connection": "keep-alive",
        },
    )
