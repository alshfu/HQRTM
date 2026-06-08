"""Applikationskonfiguration från miljövariabler (.env).

Enda källan för inställningar för web / poller / bot. Hemligheter — endast från
miljön, hårdkoda inte (publikt repo). Se .env.example.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # MongoDB (replica set krävs för Change Streams)
    mongo_uri: str = "mongodb://localhost:27017/?replicaSet=rs0"
    mongo_db: str = "hqrtm"
    # TTL för auto-rensning (DB-002/DB-003)
    seen_ttl_hours: int = 24
    listings_ttl_days: int = 7

    # Flask / web
    flask_env: str = "development"
    secret_key: str = "change-me-dev-only"
    jwt_secret: str = "change-me-dev-only"
    jwt_access_ttl_min: int = 15
    jwt_refresh_ttl_days: int = 30

    # Telegram
    telegram_bot_token: str = ""
    telegram_bot_username: str = ""

    # Poller
    poll_interval_ms: int = 3000
    hot_hours: str = "08-22"

    # HomeQ Core API (docs-core.homeq.se). Nyckel/åtkomst — från landlord-portalen
    # (homeq.se/biz → settings/integration). Adaptern aktiveras först efter ToS (COMPLIANCE.md).
    homeq_base_url: str = "https://api.homeq.se"  # demo: https://api-demo.homeq.se
    homeq_public_base: str = "https://homeq.se"  # för att bygga länkar till annonser
    homeq_username: str = ""  # integrationskonto (POST /api/v2/tokens/)
    homeq_password: str = ""
    homeq_fetch_amount: int = 100  # hur många kort som hämtas per pass (amount)
    homeq_timeout_s: float = 10.0

    # Qasa (qasa.com) — GraphQL API. ⚠️ Kontraktet är INTE officiellt verifierat,
    # åtkomst/ToS för programmatisk läsning ej bekräftad → adapter enabled=False (COMPLIANCE.md).
    qasa_api_url: str = "https://api.qasa.com/graphql"
    qasa_public_base: str = "https://qasa.com"
    qasa_fetch_amount: int = 50
    qasa_timeout_s: float = 10.0

    # Samtrygg (samtrygg.se) — uthyrning via ansökan (utan kö). ⚠️ Bas-URL/host anges inte i den
    # publika SwaggerHub-specen, ToS för programmatisk läsning ej bekräftad → adapter enabled=False
    # (COMPLIANCE.md). Före aktivering: precisera SAMTRYGG_API_URL och ToS (ägaråtgärd).
    samtrygg_api_url: str = ""  # t.ex. https://<host>/GetHomePageObjects (host saknas i specen)
    samtrygg_public_base: str = "https://samtrygg.se"  # för att bygga länkar till annonser
    samtrygg_timeout_s: float = 10.0

    # Bostadsförmedlingen i Stockholm — kommunalt öppet data-API (publik lista, ingen auth).
    # Kö-baserad (köpoäng). enabled=True i adaptern → pollern bevakar Stockholm direkt.
    bostadsformedlingen_api_url: str = "https://bostad.stockholm.se/AllaAnnonser/?vy=lista"
    bostadsformedlingen_public_base: str = "https://bostad.stockholm.se"
    bostadsformedlingen_timeout_s: float = 10.0

    # HomeQ publik bevakning (beta): pollern hämtar HomeQ:s inloggningsfria Card Search (utan JWT)
    # och filtrerar på bbox. ⚠️ Ägarens beslut/risk gällande ToS. Kontinuerlig landlord-JWT-polling
    # är fortsatt gated på ToS-bekräftelse (COMPLIANCE.md).
    homeq_public_poll: bool = False
    homeq_bbox: str = ""  # "min_lat,max_lat,min_lng,max_lng" (t.ex. Göteborg) — tom = hela landet
    homeq_public_limit: int = 50  # max antal annonser per cykel i publik bevakning

    # Observerbarhet / robusthet (Fas 8)
    log_level: str = "INFO"
    log_json: bool = False  # JSON-loggar för aggregatorer i prod
    # Lagring för rate-limit-räknare. Tom → in-memory (endast en process/dev).
    # För multiprocess/prod ange en backend, t.ex. redis://… eller memcached://…
    ratelimit_storage_uri: str = ""


@lru_cache
def get_settings() -> Settings:
    """Cachad singleton med inställningar."""
    return Settings()
