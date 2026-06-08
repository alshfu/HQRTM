"""Tester av i18n (sv/en): paritet mellan kataloger, översättning/fallback, lokal-resolv i sidor."""

from __future__ import annotations

from web.i18n import DEFAULT_LOCALE, LOCALES, TRANSLATIONS, normalize_locale, translate


def test_catalog_key_parity():
    """Nycklarna sv och en stämmer överens (inga saknade översättningar)."""
    sv = set(TRANSLATIONS["sv"])
    en = set(TRANSLATIONS["en"])
    assert sv == en, f"avvikelse i nycklar: only_sv={sv - en}, only_en={en - sv}"


def test_default_is_swedish():
    assert DEFAULT_LOCALE == "sv"
    assert set(LOCALES) == {"sv", "en"}


def test_translate_known_key():
    assert translate("login.submit", "sv") == "Logga in"
    assert translate("login.submit", "en") == "Log in"


def test_translate_unknown_locale_falls_back_to_default():
    assert translate("login.submit", "de") == "Logga in"  # de finns inte → sv


def test_translate_missing_key_returns_key():
    assert translate("nope.nope", "en") == "nope.nope"


def test_normalize_locale():
    assert normalize_locale("en") == "en"
    assert normalize_locale("sv") == "sv"
    assert normalize_locale("xx") is None
    assert normalize_locale(None) is None


# ------------------------------------------------------------------- via sidor


def test_landing_default_swedish(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert 'lang="sv"' in body
    assert "Kom igång gratis" in body  # landing.cta_start (sv)


def test_landing_english_via_query(client):
    resp = client.get("/?lang=en")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert 'lang="en"' in body
    assert "Get started free" in body  # landing.cta_start (en)
    # lokalen sparas i cookie
    assert "hqrtm_lang=en" in resp.headers.get("Set-Cookie", "")


def test_locale_persists_via_cookie(client):
    client.get("/?lang=en")  # sätter cookie
    resp = client.get("/")  # utan query — hämtas från cookie
    assert "Get started free" in resp.data.decode()


def test_invalid_lang_uses_default(client):
    resp = client.get("/?lang=xx")
    assert "Kom igång gratis" in resp.data.decode()  # standard sv


def test_js_catalog_injected(client):
    """Katalogen för aktuell lokal skickas till webbläsaren (window.HQRTM_I18N)."""
    body = client.get("/").data.decode()
    assert "window.HQRTM_I18N" in body
    assert "dashboard.fcfs_badge" in body  # nyckel från katalogen finns
