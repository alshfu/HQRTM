# Конфигурация

Все настройки — через переменные окружения (`.env`, не коммитится). Шаблон — `.env.example`.
Читаются через `shared/config.py` (`pydantic-settings`).

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `MONGO_URI` | `mongodb://localhost:27017/?replicaSet=rs0` | Подключение к MongoDB (Atlas: `mongodb+srv://…`) |
| `MONGO_DB` | `hqrtm` | Имя базы |
| `SEEN_TTL_HOURS` | `24` | TTL дедупликации (`seen_listings`) |
| `LISTINGS_TTL_DAYS` | `7` | TTL авто-очистки `listings` |
| `FLASK_ENV` | `development` | Режим Flask |
| `SECRET_KEY` | `change-me-dev-only` | Секрет Flask (сменить!) |
| `JWT_SECRET` | `change-me-dev-only` | Секрет JWT (сменить! ≥ 32 байт) |
| `JWT_ACCESS_TTL_MIN` | `15` | TTL access-токена (мин) |
| `JWT_REFRESH_TTL_DAYS` | `30` | TTL refresh-токена (дни) |
| `TELEGRAM_BOT_TOKEN` | — | Токен бота (BotFather) |
| `TELEGRAM_BOT_USERNAME` | — | Username бота (для deep-link привязки) |
| `POLL_INTERVAL_MS` | `3000` | Интервал опроса поллера |
| `HOT_HOURS` | `08-22` | Окно «горячих» часов (адаптивная частота) |
| `HOMEQ_BASE_URL` | `https://api.homeq.se` | HomeQ Core API (demo: `https://api-demo.homeq.se`) |
| `HOMEQ_PUBLIC_BASE` | `https://homeq.se` | База для ссылок на объявления HomeQ |
| `HOMEQ_USERNAME` / `HOMEQ_PASSWORD` | — | Учётка интеграции HomeQ (`/api/v2/tokens/`) |
| `HOMEQ_FETCH_AMOUNT` | `100` | Сколько карточек тянуть за проход |
| `QASA_API_URL` | `https://api.qasa.com/graphql` | Qasa GraphQL (контракт не верифицирован) |
| `QASA_PUBLIC_BASE` | `https://qasa.com` | База для ссылок на объявления Qasa |
| `QASA_FETCH_AMOUNT` | `50` | Сколько объявлений Qasa за проход |
| `LOG_LEVEL` | `INFO` | Уровень логирования |

> Адаптеры HomeQ/Qasa по умолчанию **выключены** (`enabled=False` в коде) — включение только после
> подтверждения ToS площадки (см. [Compliance](Compliance)). Учётные данные задавать после этого.

## Генерация секретов
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Безопасность
- Публичный репозиторий ⇒ **ни одного реального секрета** в коде/истории. Только `.env` (в `.gitignore`)
  и GitHub Secrets. pre-commit `detect-secrets` страхует от утечки.
- В проде обязательно сменить `SECRET_KEY` и `JWT_SECRET` на длинные случайные значения.
