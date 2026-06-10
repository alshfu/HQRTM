"""httpOnly-cookies för JWT (Fas 8, BE-AU-002).

Webbpanelen autentiserar via httpOnly-cookies (skydd mot XSS — JS kan inte läsa token).
API-klienter/tillägget fortsätter använda ``Authorization: Bearer`` (cookies sätts additivt och
stör inte Bearer-flödet). CSRF mildras av ``SameSite`` (Lax blockerar cookie vid cross-site POST).
"""

from __future__ import annotations

from flask import Response
from shared.config import get_settings

ACCESS_COOKIE = "hqrtm_access"
REFRESH_COOKIE = "hqrtm_refresh"


def set_auth_cookies(
    resp: Response, access: str | None = None, refresh: str | None = None
) -> Response:
    """Sätt access-/refresh-token som httpOnly-cookies (om ``cookie_auth`` är på)."""
    s = get_settings()
    if not s.cookie_auth:
        return resp
    common = {
        "httponly": True,
        "secure": s.cookie_secure,
        "samesite": s.cookie_samesite,
        "path": "/",
    }
    if access:
        resp.set_cookie(ACCESS_COOKIE, access, max_age=s.jwt_access_ttl_min * 60, **common)
    if refresh:
        resp.set_cookie(REFRESH_COOKIE, refresh, max_age=s.jwt_refresh_ttl_days * 86400, **common)
    return resp


def clear_auth_cookies(resp: Response) -> Response:
    """Ta bort auth-cookies (utloggning)."""
    s = get_settings()
    for name in (ACCESS_COOKIE, REFRESH_COOKIE):
        resp.delete_cookie(name, path="/", samesite=s.cookie_samesite)
    return resp
