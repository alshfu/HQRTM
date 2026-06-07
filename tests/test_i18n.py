"""Тесты i18n (sv/en): паритет каталогов, перевод/fallback, резолв локали в страницах."""

from __future__ import annotations

from web.i18n import DEFAULT_LOCALE, LOCALES, TRANSLATIONS, normalize_locale, translate


def test_catalog_key_parity():
    """Ключи sv и en совпадают (нет пропусков перевода)."""
    sv = set(TRANSLATIONS["sv"])
    en = set(TRANSLATIONS["en"])
    assert sv == en, f"расхождение ключей: only_sv={sv - en}, only_en={en - sv}"


def test_default_is_swedish():
    assert DEFAULT_LOCALE == "sv"
    assert set(LOCALES) == {"sv", "en"}


def test_translate_known_key():
    assert translate("login.submit", "sv") == "Logga in"
    assert translate("login.submit", "en") == "Log in"


def test_translate_unknown_locale_falls_back_to_default():
    assert translate("login.submit", "de") == "Logga in"  # де нет → sv


def test_translate_missing_key_returns_key():
    assert translate("nope.nope", "en") == "nope.nope"


def test_normalize_locale():
    assert normalize_locale("en") == "en"
    assert normalize_locale("sv") == "sv"
    assert normalize_locale("xx") is None
    assert normalize_locale(None) is None


# ------------------------------------------------------------------- через страницы


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
    # локаль уходит в cookie
    assert "hqrtm_lang=en" in resp.headers.get("Set-Cookie", "")


def test_locale_persists_via_cookie(client):
    client.get("/?lang=en")  # ставит cookie
    resp = client.get("/")  # без query — берётся из cookie
    assert "Get started free" in resp.data.decode()


def test_invalid_lang_uses_default(client):
    resp = client.get("/?lang=xx")
    assert "Kom igång gratis" in resp.data.decode()  # дефолт sv


def test_js_catalog_injected(client):
    """Каталог текущей локали уходит в браузер (window.HQRTM_I18N)."""
    body = client.get("/").data.decode()
    assert "window.HQRTM_I18N" in body
    assert "dashboard.fcfs_badge" in body  # ключ из каталога присутствует
