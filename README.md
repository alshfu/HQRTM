# HQRTM — HomeQ Real-Time Monitor

Сервис круглосуточно отслеживает публикации **HomeQ**, мгновенно выделяет объявления типа
**«Först till kvarn» (FCFS)**, сопоставляет их с фильтрами пользователей и доставляет уведомление
со ссылкой в **Telegram за ≤ 1.5 с**. Веб-кабинет позволяет настраивать фильтры, привязывать
Telegram и видеть живую ленту совпадений.

> Бот **не** логинится в аккаунт HomeQ и **не** подаёт заявки — только уведомляет.

🔗 **Demo (UI, мок-данные):** https://alshfu.github.io/HQRTM/

## Стек

Flask 3 (API + Jinja2) · MongoDB (PyMongo + Motor) · отдельный asyncio-поллер (`httpx`) ·
Telegram (`aiogram`) · real-time через MongoDB Change Streams + SSE · Vanilla JS.

Полное ТЗ: [`HQRTM_ToR_Flask_MongoDB_Roadmap.md`](HQRTM_ToR_Flask_MongoDB_Roadmap.md) (канон).
Руководство для разработки (в т.ч. для ИИ-ассистентов): [`CLAUDE.md`](CLAUDE.md).

## Архитектура (процессы)

| Процесс | Назначение |
|---|---|
| `poller` | asyncio: опрос HomeQ → детекция FCFS → матчинг → постановка уведомлений |
| `bot`    | Telegram-бот (aiogram): привязка, отправка уведомлений |
| `web`    | Flask: REST API, веб-кабинет, SSE-лента |
| MongoDB  | хранилище + Change Streams (replica set) |

Поллер вынесен в **отдельный процесс**: высокочастотный опрос 24/7 несовместим с request-response
моделью Flask. Связь между процессами — через MongoDB.

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

# 5. Запуск веб-приложения (API + кабинет)
flask --app web.app run --debug      # http://127.0.0.1:5000/  (кабинет), /health, /apidocs

# 6. Запуск поллера (отдельный процесс) — появится в Фазе 2
# python -m poller.main

# 7. Запуск Telegram-бота (отдельный процесс) — появится в Фазе 3
# python -m bot.main
```

### API (Фаза 4, частично)

| Метод | Endpoint | Назначение |
|---|---|---|
| POST | `/auth/register`, `/auth/login`, `/auth/refresh` | Регистрация/вход (JWT access+refresh) |
| GET/POST/PUT/DELETE | `/api/filters[/<id>]` | CRUD фильтров (нужен `Authorization: Bearer`) |
| GET/DELETE | `/api/me` | Профиль; удаление аккаунта и данных (GDPR) |
| GET | `/health` | Health-check |

Пароли — Argon2; доступ к данным — только своим (проверка по JWT). _В планах Фазы 4:_
`/api/listings`, `/api/notifications`, `/api/telegram/*`, OpenAPI/Swagger.

## Конфигурация

Все настройки — через переменные окружения (см. [`.env.example`](.env.example)).
Частота опроса: `POLL_INTERVAL_MS` (безопасный дефолт; учащение в «горячие» часы — `HOT_HOURS`).

## Разработка

```bash
ruff check .        # линт
black .             # формат
pytest              # тесты
```

Ветвление: `main` (стабильная) ← `develop` ← `feature/*`, изменения через PR.

## Статус

Проект в активной разработке по [roadmap](HQRTM_ToR_Flask_MongoDB_Roadmap.md#11-roadmap--пошаговая-реализация).
Текущая фаза и прогресс фиксируются в [`CLAUDE.md`](CLAUDE.md).

## Лицензия

[MIT](LICENSE) · Комплаенс (ToS HomeQ + GDPR): [`COMPLIANCE.md`](COMPLIANCE.md).
