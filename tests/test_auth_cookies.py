"""Tester för httpOnly-cookie-auth (Fas 8, BE-AU-002).

Flask-testklienten har en cookie-jar → vi kan verifiera hela cookie-flödet:
login sätter httpOnly-cookies, skyddade endpoints accepterar cookien (utan Bearer),
refresh läser refresh-cookien, logout rensar allt.
"""

from __future__ import annotations

from web.auth.cookies import ACCESS_COOKIE, REFRESH_COOKIE


def _set_cookie_headers(resp) -> list[str]:
    return [v for k, v in resp.headers if k == "Set-Cookie"]


def test_login_sets_httponly_cookies(client, make_user):
    make_user()
    resp = client.post("/auth/login", json={"email": "elin@hqrtm.se", "password": "demo1234"})
    assert resp.status_code == 200
    cookies = "\n".join(_set_cookie_headers(resp))
    assert ACCESS_COOKIE in cookies and REFRESH_COOKIE in cookies
    assert "HttpOnly" in cookies
    assert "SameSite=Lax" in cookies
    # tokens returneras fortfarande i JSON för Bearer-klienter (tillägget)
    assert "access_token" in resp.get_json()


def test_protected_endpoint_accepts_cookie(client, make_user):
    # make_user registrerar → testklienten får auth-cookies i sin jar
    make_user()
    # ingen Authorization-header: åtkomst sker enbart via cookien
    resp = client.get("/api/filters")
    assert resp.status_code == 200
    assert resp.get_json()["items"] == []


def test_refresh_reads_refresh_cookie_without_body(client, make_user):
    make_user()
    resp = client.post("/auth/refresh")  # ingen body → servern läser refresh-cookien
    assert resp.status_code == 200
    assert "access_token" in resp.get_json()
    assert any(ACCESS_COOKIE in h for h in _set_cookie_headers(resp))


def test_logout_clears_cookies_and_blocks_access(client, make_user):
    make_user()
    assert client.get("/api/filters").status_code == 200  # inloggad via cookie

    client.post("/auth/logout")
    # cookie-jar tömd av servern (Max-Age=0) → skyddad endpoint nekar
    assert client.get("/api/filters").status_code == 401


def test_bearer_still_works_alongside_cookies(client, make_user, bearer):
    data = make_user()
    # även om klienten har en cookie ska en explicit Bearer-header respekteras
    resp = client.get("/api/filters", headers=bearer(data["access_token"]))
    assert resp.status_code == 200
