"""Lättviktig i18n utan tredjepartsbibliotek (sv prioriterad, en sekundär).

Ansats i kanonens anda (Vanilla JS + Jinja2): ordbokskataloger i stället för flask-babel.
Samma katalog skickas till mallar (`t()`) och till webbläsaren (`window.HQRTM_I18N`),
därför översätts inline-JS-strängar med samma nyckel via `HQRTM.t()`.

Locale bestäms av: `?lang=sv|en` → cookie `hqrtm_lang` → standard `sv`.
Svenska är marknadens språk (prioritet, beslut 2026-06-07); engelska — fallback vid saknad nyckel.
"""

from __future__ import annotations

from flask import Flask, Response, g, request

DEFAULT_LOCALE = "sv"
LOCALES: tuple[str, ...] = ("sv", "en")
COOKIE = "hqrtm_lang"
_COOKIE_MAX_AGE = 365 * 24 * 3600

# Översättningskataloger. Nycklarna MÅSTE matcha mellan sv och en (kontrolleras av test).
TRANSLATIONS: dict[str, dict[str, str]] = {
    "sv": {
        # nav / gemensamt
        "nav.feed": "Flöde",
        "nav.filters": "Filter",
        "nav.notifications": "Aviseringar",
        "nav.account": "Konto",
        "nav.admin": "Admin",
        "nav.logout": "Logga ut",
        "app.subtitle": "Real-Time Monitor",
        "role.admin": "Administratör",
        "role.user": "Användare",
        "common.email": "E-post",
        "common.password": "Lösenord",  # pragma: allowlist secret
        "common.email_placeholder": "namn@exempel.se",
        "unit.rooms": "rok",
        "unit.kr": "kr",
        "unit.rent_month": "kr/mån",
        "unit.items": "st",
        # landing
        "landing.title": "HQRTM — bevakning av svenska bostäder",
        "landing.kicker": "HomeQ Real-Time Monitor",
        "landing.h1_a": "All-in-one bevakning av",
        "landing.h1_b": "svenska bostäder",
        "landing.lead": (
            "Bevakar flera plattformar (HomeQ, Qasa, Blocket Bostad m.fl.), lyfter fram "
            "«Först till kvarn» och skickar avisering till Telegram på sekunder."
        ),
        "landing.cta_start": "Kom igång gratis",
        "landing.cta_login": "Logga in",
        "landing.demo": "UI-demo (mock-data)",
        "landing.apidocs": "API-docs",
        # login
        "login.title": "Logga in — HQRTM",
        "login.h1": "Välkommen tillbaka",
        "login.lead": "Logga in för att se ditt flöde.",
        "login.submit": "Logga in",
        "login.no_account": "Inget konto?",
        "login.register_link": "Registrera dig",
        "login.err_credentials": "Fel e-post eller lösenord",
        "login.err_failed": "Inloggning misslyckades",
        # register
        "register.title": "Registrera — HQRTM",
        "register.h1": "Skapa konto",
        "register.lead": "Börja bevaka bostäder på sekunder.",
        "register.pw_placeholder": "Minst 8 tecken",
        "register.consent_a": "Jag godkänner",
        "register.consent_terms": "villkoren",
        "register.consent_and": "och",
        "register.consent_privacy": "integritetspolicyn",
        "register.submit": "Registrera dig",
        "register.have_account": "Har du konto?",
        "register.login_link": "Logga in",
        "register.err_consent": "Du måste godkänna villkoren",
        "register.err_pw": "Lösenordet måste vara minst 8 tecken",
        "register.err_taken": "E-posten är redan registrerad",
        "register.err_failed": "Registrering misslyckades",
        # dashboard / feed
        "dashboard.title": "Flöde — HQRTM",
        "dashboard.heading": "Flöde",
        "dashboard.sub": "Bostäder som matchat dina filter.",
        "dashboard.only_matched": "Endast matchade",
        "dashboard.reload": "Uppdatera",
        "dashboard.empty": "Inga bostäder ännu.",
        "dashboard.fcfs_badge": "FÖRST TILL KVARN",
        "dashboard.open": "Öppna →",
        "dashboard.apply": "Ansök →",
        "dashboard.err_load": "Kunde inte ladda flödet",
        "live.connecting": "ansluter…",
        "live.live": "live",
        "live.reconnecting": "återansluter…",
        "live.polling": "polling",
        # filters
        "filters.title": "Filter — HQRTM",
        "filters.heading": "Filter",
        "filters.sub": "Skapa och hantera dina bevakningsfilter.",
        "filters.name_placeholder": "Namn (t.ex. Söder 2 rok)",
        "filters.district_placeholder": "Område",
        "filters.city_placeholder": "Stad",
        "filters.rent_max_placeholder": "Max hyra (kr)",
        "filters.rooms_min_placeholder": "Min rum",
        "filters.only_fcfs": "Endast «Först till kvarn»",
        "filters.add": "Lägg till filter",
        "filters.empty": "Inga filter ännu.",
        "filters.active": "aktivt",
        "filters.paused": "pausat",
        "filters.pause": "Pausa",
        "filters.activate": "Aktivera",
        "filters.delete": "Ta bort",
        "filters.err_load": "Kunde inte ladda filter",
        "filters.added": "Filter tillagt",
        "filters.err_save": "Kunde inte spara filtret",
        "filters.removed": "Filter borttaget",
        # notifications
        "notifications.title": "Aviseringar — HQRTM",
        "notifications.heading": "Aviseringar",
        "notifications.sub": "Historik över skickade aviseringar.",
        "notifications.empty": "Inga aviseringar ännu.",
        "notifications.err_load": "Kunde inte ladda historiken",
        # settings
        "settings.title": "Konto — HQRTM",
        "settings.heading": "Konto",
        "settings.sub": "Profil, Telegram-koppling och radering av konto.",
        "settings.profile": "Profil",
        "settings.email_label": "E-post:",
        "settings.role_label": "Roll:",
        "settings.telegram": "Telegram",
        "settings.status_label": "Status:",
        "settings.tg_connect": "Koppla Telegram",
        "settings.tg_instr": "Öppna länken eller ange koden i boten:",
        "settings.tg_code": "Kod:",
        "settings.tg_linked": "Kopplad ✓",
        "settings.tg_unlinked": "Ej kopplad",
        "settings.tg_nobot": "(bot-användarnamn ej konfigurerat)",
        "settings.tg_err": "Kunde inte skapa länk",
        "settings.delete_title": "Radera konto (GDPR)",
        "settings.delete_desc": "Tar bort kontot och alla data permanent. Kan inte ångras.",
        "settings.delete_btn": "Radera mitt konto",
        "settings.delete_confirm": "Radera kontot och all data permanent?",
        "settings.delete_err": "Kunde inte radera kontot",
        # admin
        "admin.title": "Admin — HQRTM",
        "admin.heading": "Admin",
        "admin.sub": "Översikt och användarhantering.",
        "admin.stat_users": "Användare",
        "admin.stat_filters": "Filter",
        "admin.stat_listings": "Bostäder",
        "admin.stat_notifications": "Aviseringar",
        "admin.users_title": "Användare",
        "admin.col_email": "E-post",
        "admin.col_role": "Roll",
        "admin.col_status": "Status",
        "admin.col_created": "Skapad",
        "admin.col_actions": "Åtgärder",
        "admin.make_admin": "Gör till admin",
        "admin.make_user": "Gör till användare",
        "admin.you": "(du)",
        "admin.err_load": "Kunde inte ladda data",
        "admin.role_changed": "Roll uppdaterad",
        "admin.err_role": "Kunde inte ändra roll",
        "admin.forbidden": "Endast för administratörer",
    },
    "en": {
        # nav / common
        "nav.feed": "Feed",
        "nav.filters": "Filters",
        "nav.notifications": "Notifications",
        "nav.account": "Account",
        "nav.admin": "Admin",
        "nav.logout": "Log out",
        "app.subtitle": "Real-Time Monitor",
        "role.admin": "Administrator",
        "role.user": "User",
        "common.email": "Email",
        "common.password": "Password",  # pragma: allowlist secret
        "common.email_placeholder": "name@example.com",
        "unit.rooms": "rooms",
        "unit.kr": "SEK",
        "unit.rent_month": "SEK/mo",
        "unit.items": "items",
        # landing
        "landing.title": "HQRTM — Swedish housing monitor",
        "landing.kicker": "HomeQ Real-Time Monitor",
        "landing.h1_a": "All-in-one monitoring of",
        "landing.h1_b": "Swedish housing",
        "landing.lead": (
            "Monitors multiple platforms (HomeQ, Qasa, Blocket Bostad and more), highlights "
            "“first come, first served” and sends a Telegram alert within seconds."
        ),
        "landing.cta_start": "Get started free",
        "landing.cta_login": "Log in",
        "landing.demo": "UI demo (mock data)",
        "landing.apidocs": "API docs",
        # login
        "login.title": "Log in — HQRTM",
        "login.h1": "Welcome back",
        "login.lead": "Log in to see your feed.",
        "login.submit": "Log in",
        "login.no_account": "No account?",
        "login.register_link": "Sign up",
        "login.err_credentials": "Wrong email or password",
        "login.err_failed": "Login failed",
        # register
        "register.title": "Sign up — HQRTM",
        "register.h1": "Create account",
        "register.lead": "Start monitoring homes in seconds.",
        "register.pw_placeholder": "At least 8 characters",
        "register.consent_a": "I accept the",
        "register.consent_terms": "terms",
        "register.consent_and": "and",
        "register.consent_privacy": "privacy policy",
        "register.submit": "Sign up",
        "register.have_account": "Already have an account?",
        "register.login_link": "Log in",
        "register.err_consent": "You must accept the terms",
        "register.err_pw": "Password must be at least 8 characters",
        "register.err_taken": "Email is already registered",
        "register.err_failed": "Registration failed",
        # dashboard / feed
        "dashboard.title": "Feed — HQRTM",
        "dashboard.heading": "Feed",
        "dashboard.sub": "Homes matching your filters.",
        "dashboard.only_matched": "Matched only",
        "dashboard.reload": "Refresh",
        "dashboard.empty": "No homes yet.",
        "dashboard.fcfs_badge": "FIRST COME, FIRST SERVED",
        "dashboard.open": "Open →",
        "dashboard.apply": "Apply →",
        "dashboard.err_load": "Could not load the feed",
        "live.connecting": "connecting…",
        "live.live": "live",
        "live.reconnecting": "reconnecting…",
        "live.polling": "polling",
        # filters
        "filters.title": "Filters — HQRTM",
        "filters.heading": "Filters",
        "filters.sub": "Create and manage your monitoring filters.",
        "filters.name_placeholder": "Name (e.g. Söder 2 rooms)",
        "filters.district_placeholder": "District",
        "filters.city_placeholder": "City",
        "filters.rent_max_placeholder": "Max rent (SEK)",
        "filters.rooms_min_placeholder": "Min rooms",
        "filters.only_fcfs": "“First come, first served” only",
        "filters.add": "Add filter",
        "filters.empty": "No filters yet.",
        "filters.active": "active",
        "filters.paused": "paused",
        "filters.pause": "Pause",
        "filters.activate": "Activate",
        "filters.delete": "Delete",
        "filters.err_load": "Could not load filters",
        "filters.added": "Filter added",
        "filters.err_save": "Could not save the filter",
        "filters.removed": "Filter removed",
        # notifications
        "notifications.title": "Notifications — HQRTM",
        "notifications.heading": "Notifications",
        "notifications.sub": "History of sent notifications.",
        "notifications.empty": "No notifications yet.",
        "notifications.err_load": "Could not load the history",
        # settings
        "settings.title": "Account — HQRTM",
        "settings.heading": "Account",
        "settings.sub": "Profile, Telegram link and account deletion.",
        "settings.profile": "Profile",
        "settings.email_label": "Email:",
        "settings.role_label": "Role:",
        "settings.telegram": "Telegram",
        "settings.status_label": "Status:",
        "settings.tg_connect": "Connect Telegram",
        "settings.tg_instr": "Open the link or enter the code in the bot:",
        "settings.tg_code": "Code:",
        "settings.tg_linked": "Connected ✓",
        "settings.tg_unlinked": "Not connected",
        "settings.tg_nobot": "(bot username not configured)",
        "settings.tg_err": "Could not create link",
        "settings.delete_title": "Delete account (GDPR)",
        "settings.delete_desc": "Permanently deletes your account and all data. Cannot be undone.",
        "settings.delete_btn": "Delete my account",
        "settings.delete_confirm": "Permanently delete your account and all data?",
        "settings.delete_err": "Could not delete the account",
        # admin
        "admin.title": "Admin — HQRTM",
        "admin.heading": "Admin",
        "admin.sub": "Overview and user management.",
        "admin.stat_users": "Users",
        "admin.stat_filters": "Filters",
        "admin.stat_listings": "Listings",
        "admin.stat_notifications": "Notifications",
        "admin.users_title": "Users",
        "admin.col_email": "Email",
        "admin.col_role": "Role",
        "admin.col_status": "Status",
        "admin.col_created": "Created",
        "admin.col_actions": "Actions",
        "admin.make_admin": "Make admin",
        "admin.make_user": "Make user",
        "admin.you": "(you)",
        "admin.err_load": "Could not load data",
        "admin.role_changed": "Role updated",
        "admin.err_role": "Could not change role",
        "admin.forbidden": "Administrators only",
    },
}


def normalize_locale(value: str | None) -> str | None:
    """Returnera locale om den stöds, annars None."""
    return value if value in LOCALES else None


def translate(key: str, locale: str | None = None, **kwargs) -> str:
    """Översätt nyckeln. Fallback: begärd locale → standard (sv) → själva nyckeln."""
    loc = normalize_locale(locale) or DEFAULT_LOCALE
    value = TRANSLATIONS[loc].get(key)
    if value is None:
        value = TRANSLATIONS[DEFAULT_LOCALE].get(key, key)
    if kwargs:
        try:
            value = value.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            pass
    return value


def init_i18n(app: Flask) -> None:
    """Koppla in i18n: resolva locale, spara i cookie, Jinja-globaler."""

    @app.before_request
    def _resolve_locale() -> None:
        chosen = normalize_locale(request.args.get("lang"))
        if chosen:
            g.locale = chosen
            g.persist_locale = chosen
        else:
            cookie = normalize_locale(request.cookies.get(COOKIE))
            g.locale = cookie or DEFAULT_LOCALE
            g.persist_locale = None

    @app.after_request
    def _persist_locale(resp: Response) -> Response:
        lang = getattr(g, "persist_locale", None)
        if lang:
            resp.set_cookie(COOKIE, lang, max_age=_COOKIE_MAX_AGE, samesite="Lax")
        return resp

    @app.context_processor
    def _inject() -> dict:
        loc = getattr(g, "locale", DEFAULT_LOCALE)
        return {
            "t": lambda key, **kw: translate(key, loc, **kw),
            "locale": loc,
            "locales": LOCALES,
            "i18n_catalog": TRANSLATIONS[loc],
        }
