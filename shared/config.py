"""Конфигурация приложения из переменных окружения (.env).

Единый источник настроек для web / poller / bot. Секреты — только из окружения,
не хардкодить (публичный репозиторий). См. .env.example.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # MongoDB (replica set обязателен для Change Streams)
    mongo_uri: str = "mongodb://localhost:27017/?replicaSet=rs0"
    mongo_db: str = "hqrtm"
    # TTL авто-очистки (DB-002/DB-003)
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
    homeq_base_url: str = ""
    hot_hours: str = "08-22"

    # Логирование
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Кэшированный синглтон настроек."""
    return Settings()
