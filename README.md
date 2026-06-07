# HQRTM — HomeQ Real-Time Monitor

**All-in-one агрегатор** мониторинга аренды жилья на нескольких шведских площадках
(HomeQ, Qasa, далее — Blocket Bostad, Bostad Direkt, Samtrygg…). Круглосуточно отслеживает
публикации, мгновенно выделяет объявления типа **«Först till kvarn» (FCFS)**, отсеивает
очередные, сопоставляет с фильтрами пользователей и доставляет уведомление со ссылкой
в **Telegram за ≤ 1.5 с**. Веб-кабинет: фильтры, привязка Telegram, живая лента (SSE),
интерфейс на **шведском и английском**.

> Бот **не** логинится в аккаунты площадок и **не** подаёт заявки — только уведомляет.

🔗 **Demo (UI, мок-данные):** https://alshfu.github.io/HQRTM/

## Стек

Flask 3 (API + Jinja2) · MongoDB (PyMongo + Motor) · отдельный asyncio-поллер (`httpx`) ·
Telegram (`aiogram`) · real-time через MongoDB Change Streams + SSE · Vanilla JS ·
Tailwind CSS (production-сборка) · i18n sv/en.

Полное ТЗ: [`HQRTM_ToR_Flask_MongoDB_Roadmap.md`](HQRTM_ToR_Flask_MongoDB_Roadmap.md) (канон).
Руководство для разработки (в т.ч. для ИИ-ассистентов): [`CLAUDE.md`](CLAUDE.md).
Подробная документация — [**Wiki**](https://github.com/alshfu/HQRTM/wiki) (исходники в [`docs/wiki/`](docs/wiki/)).

## Мульти-source

Источник изолирован в адаптере (`poller/sources/`, база `SourceAdapter` + реестр). Все площадки
нормализуются в одну коллекцию `listings`; уникальность объявления — пара **(source, external_id)**.
Добавить площадку = новый адаптер, ядро поллера не меняется.

| Площадка | Адаптер | Путь | Статус |
|---|---|---|---|
| HomeQ | `poller/sources/homeq.py` | официальный **Core API** (`/api/v2/tokens/` + Card Search) | реализован, `enabled=False` (нужны ключ + ToS) |
| Qasa  | `poller/sources/qasa.py`  | GraphQL `homes` | реализован, контракт не верифицирован, `enabled=False` |

> ⚠️ Адаптер включается (`enabled=True`) только после проверки ToS площадки — см. [`COMPLIANCE.md`](COMPLIANCE.md).

## Архитектура (процессы)

| Процесс | Назначение |
|---|---|
| `poller` | asyncio: опрос площадок → детекция FCFS → дедуп → матчинг с фильтрами → постановка уведомлений |
| `bot`    | Telegram-бот (aiogram): привязка аккаунта, доставка уведомлений (Фаза 3) |
| `web`    | Flask: REST API, веб-кабинет, SSE-лента, админ-панель |
| MongoDB  | хранилище + Change Streams (replica set) |

Поллер вынесен в **отдельный процесс**: высокочастотный опрос 24/7 несовместим с request-response
моделью Flask. Связь между процессами — через MongoDB (поллер пишет, web читает + слушает Change Stream).

## Локальный запуск (dev)

Требуется **Python 3.12+** и доступ к MongoDB с replica set (рекомендуется **Atlas free-tier** —
replica set из коробки).

```bash
# 1. Окружение
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 2. Секреты
cp .env.example .env        # заполните MONGO_URI (Atlas) и прочее

# 3. Pre-commit хуки (защита public repo от утечки секретов)
pre-commit install

# 4. Индексы MongoDB (один раз на новой БД)
python -m shared.db

# 5. Запуск веб-приложения (API + кабинет + админ-панель + SSE)
flask --app web.app run --debug      # http://127.0.0.1:5000/ , /health , /apidocs

# 6. Поллер (отдельный процесс). Без включённых адаптеров (enabled=True) лог скажет, что их нет.
# python -m poller.main

# 7. Telegram-бот (отдельный процесс) — Фаза 3
# python -m bot.main
```

CSS уже собран и закоммичен (`web/static/css/app.css`) — Node для запуска не нужен.
Пересборка стилей после правки шаблонов: `cd frontend-build && npm install && npm run build`
(см. [`frontend-build/README.md`](frontend-build/README.md)).

## REST API

| Метод | Endpoint | Назначение |
|---|---|---|
| POST | `/auth/register`, `/auth/login`, `/auth/refresh` | Регистрация/вход (JWT access+refresh) |
| GET/POST/PUT/DELETE | `/api/filters[/<id>]` | CRUD фильтров |
| GET | `/api/listings` | Лента (`?matched=true`, `source`, `listing_type`, `district`, пагинация) |
| GET | `/api/notifications` | История уведомлений (пагинация) |
| POST/GET | `/api/telegram/link`, `/api/telegram/status` | Привязка Telegram |
| GET/DELETE | `/api/me` | Профиль; удаление аккаунта и данных (GDPR) |
| GET/POST | `/api/admin/stats`, `/api/admin/users`, `/api/admin/users/<id>/role` | Админ-панель (роль `admin`) |
| GET | `/sse/feed` | Живая лента совпадений (SSE, auth по `?token=`) |
| GET | `/health`, `/openapi.json`, `/apidocs` | Health-check, OpenAPI, Swagger UI |

Пароли — Argon2; доступ к данным — только своим (проверка по JWT). Полный справочник —
[Wiki → API-Reference](docs/wiki/API-Reference.md).

## Интернационализация

Интерфейс на **шведском (приоритет)** и **английском**. Локаль: `?lang=sv|en` → cookie → дефолт `sv`.
Каталоги — `web/i18n.py` (без сторонних библиотек); переключатель языка в UI.

## Конфигурация

Все настройки — через переменные окружения (см. [`.env.example`](.env.example) и
[Wiki → Configuration](docs/wiki/Configuration.md)).
Частота опроса: `POLL_INTERVAL_MS` (безопасный дефолт; учащение в «горячие» часы — `HOT_HOURS`).

## Разработка

```bash
ruff check .        # линт
black .             # формат
pytest              # тесты (110 passed)
```

Ветвление: `main` (стабильная) ← `develop` ← `feature/*`, изменения через PR.
CI (`.github/workflows/ci.yml`): ruff + black + pytest на push/PR в `main`/`develop`.

## Статус

Готово: **Фазы 0, 1, 2 (ядро + адаптеры HomeQ/Qasa), 4, 5, 6, 7**. В работе/впереди: Telegram-доставка
(Фаза 3), устойчивость/безопасность (8), деплой на VPS (10). Реальный опрос площадок ждёт включения
адаптеров (ключи/ToS — решение владельца). Актуальный прогресс — [`CLAUDE.md`](CLAUDE.md) и
[Wiki → Roadmap](docs/wiki/Roadmap-and-Changelog.md).

## Лицензия

[MIT](LICENSE) · Комплаенс (ToS площадок + GDPR): [`COMPLIANCE.md`](COMPLIANCE.md).
