# CLAUDE.md — руководство для ИИ-ассистента по проекту HQRTM

> Этот файл — точка входа для любого ИИ-ассистента (Claude Code и др.), работающего над проектом.
> Читай его **первым**, до любых действий. Поддерживай его в актуальном состоянии: после
> значимых решений и изменений — обновляй разделы «Текущее состояние» и «Журнал решений» внизу.

---

## 1. Что это за проект

**HQRTM** — **all-in-one агрегатор** мониторинга аренды жилья на нескольких шведских площадках
(HomeQ — первая; далее Qasa, Blocket Bostad, Bostad Direkt, Samtrygg, Bostadsförmedlingen, Boplats…).
Круглосуточно мониторит публикации, мгновенно выделяет объявления типа **«Först till kvarn» (FCFS)**,
отсеивает «очередные» (queue), сопоставляет с фильтрами пользователей и доставляет уведомление
со ссылкой в **Telegram за ≤ 1.5 с**. Веб-кабинет: фильтры, привязка Telegram, живая лента.

> **Мульти-source (решение 2026-06-07):** источник изолирован в адаптере `poller/sources/`
> (база `SourceAdapter` + реестр). Все площадки нормализуются в одну коллекцию `listings`
> с полем `source`; уникальность объявления — пара **(source, external_id)**. Добавить площадку =
> новый адаптер, ядро поллера не меняется. ⚠️ ToS/robots.txt — **отдельно по каждой площадке**
> (чек-лист в `COMPLIANCE.md`); адаптер `enabled=True` только после положительного вывода.

**Вне scope (важно):** бот **не** логинится в аккаунты площадок и **не** подаёт заявки — только уведомляет.

---

## 2. ⚠️ ГЛАВНОЕ: какой стек считать каноническим

В репозитории три ТЗ, и они **противоречат друг другу по технологиям**. Это не ошибка чтения —
это эволюция замысла. Каноническим является **последний и самый детальный** документ:

### ✅ Источник истины: `HQRTM_ToR_Flask_MongoDB_Roadmap.md`

Утверждённый стек:

| Слой | Технология |
|---|---|
| Backend API + Web | **Flask 3.x** (Python 3.12+) + **Jinja2** шаблоны |
| Поллер / воркер | **Отдельный** asyncio-процесс: `httpx` + `asyncio` (+ `Playwright` fallback) |
| Telegram | `aiogram` (async) |
| База данных | **MongoDB** (PyMongo для Flask, Motor для async-воркера) |
| Real-time | **MongoDB Change Streams + SSE** (`EventSource`), НЕ WebSocket |
| Frontend стили | **Tailwind CSS** или **Bootstrap 5** (выбор ещё не зафиксирован — см. §6) |
| Frontend логика | **Vanilla JavaScript** (`fetch`, `EventSource`), НЕ React |
| Репозиторий | **GitHub public** |
| Demo | **GitHub Pages** (статика + мок-данные) |
| Деплой | Docker + docker-compose на VPS, Nginx + TLS |

### ⚠️ Устаревшие/альтернативные ТЗ — НЕ реализовывать как есть

- **`HQRTM_ToR_Backend.md`** — ранний proposal: FastAPI + PostgreSQL + Redis + WebSocket.
  Используй его **только** как источник детальных требований (ID вида `BE-DE-001`, бюджет
  латентности, NFR, риски). Конкретные технологии (FastAPI/Postgres/Redis) **заменены** на
  Flask/MongoDB/Change Streams в Roadmap. SQL-схема в нём — концептуальная; реальная модель
  данных — в Roadmap §3 (MongoDB-коллекции).
- **`HQRTM_ToR_Frontend.md`** — ранний proposal фронтенда: React + TypeScript + Vite + WebSocket.
  Тоже используй как источник UX-требований (ID `FE-AU-001` и т. д.), но технология —
  Jinja2 + Vanilla JS по Roadmap, не React/SPA.

**Если требование противоречит между документами — Roadmap побеждает.** Если сомневаешься,
к какому стеку относится задача, — спроси пользователя, не выбирай молча.

> Терминология: в Backend ToR real-time называется `WS /ws/feed` (WebSocket). В каноническом
> стеке это **SSE `/sse/feed`**. Не путать.

---

## 3. Текущее состояние проекта (на 2026-06-07)

**Кода приложения ещё нет**, но git и публикация demo уже настроены. В репозитории:

```
HQRTM/
├── HQRTM_ToR_Flask_MongoDB_Roadmap.md   # ✅ канон: стек + полный roadmap (фазы 0–11)
├── HQRTM_ToR_Backend.md                 # ⚠️ ранний proposal (требования — да, стек — нет)
├── HQRTM_ToR_Frontend.md                # ⚠️ ранний proposal (требования — да, стек — нет)
├── CLAUDE.md                            # этот файл
├── index.html                           # витрина GitHub Pages: CTA на приложение + device-снапшоты + демо-доступы
├── HQRTM-Demo/
│   ├── index.html                       # ✅ основное демо: модульное React-приложение (Babel в браузере)
│   ├── app/*.jsx  styles/*.css  tweaks-panel.jsx   # модули модульной версии (грузятся по HTTP)
│   └── HQRTM-{Desktop,Tablet,Mobile}.html          # self-contained device-снапшоты (frame-locked)
├── pyproject.toml                       # зависимости + ruff/black/pytest (источник истины)
├── .env.example  README.md  COMPLIANCE.md  CONTRIBUTING.md  LICENSE(MIT)
├── .pre-commit-config.yaml  .secrets.baseline   # ruff/black/detect-secrets
├── .github/workflows/ci.yml             # CI: ruff + black + pytest (push/PR в main|develop)
├── shared/   # config.py (pydantic-settings), db.py, models.py, utils.py
├── web/      # app.py (Flask factory + /health), auth/ api/ sse/ templates/ static/
├── poller/   # main.py, homeq_adapter.py, detector.py, matcher.py, dispatcher.py (заглушки)
├── bot/      # main.py, handlers.py (заглушки)
├── tests/    # test_smoke.py, test_utils.py
├── .gitignore                           # защита public repo (.env, .venv, .idea, ...)
├── .venv/  (ignored)                    # Python 3.12
└── .idea/  (ignored)
```

**Готово:**
- ✅ Git: репо **https://github.com/alshfu/HQRTM** (public). Ветки `main` (стабильная) и `develop`.
- ✅ GitHub Pages: **https://alshfu.github.io/HQRTM/** (source `main`/корень) — demo отдаётся (200).
- ✅ **Фаза 0 завершена** (код): структура пакетов, `pyproject.toml`, venv 3.12, `.env.example`,
  README/COMPLIANCE/CONTRIBUTING/LICENSE(MIT), pre-commit (ruff/black/detect-secrets), CI `ci.yml`.
  Линт/формат/тесты зелёные (`ruff`, `black --check`, `pytest` — 10 passed). `web/app.py` отдаёт `/health`.
- ⚠️ Шаблонный `main.py` (PyCharm) удалён.

**Ещё НЕ сделано:** GitHub Wiki (скелет), GitHub Project/Issues — опционально; `COMPLIANCE.md`
заполнен только скелетом (ToS HomeQ + GDPR — TODO до Фазы 2). Дальше — **Фаза 1** (слой данных MongoDB).

> ⚠️ Демо в `HQRTM-Demo/` — это **дизайн-прототипы** (React + Babel-in-browser, мок-данные), не итоговый фронтенд.
> Боевой фронтенд по канону — Jinja2 + Tailwind/Bootstrap внутри `web/` (Фаза 5). Прототипы — референс UI.
>
> Демо-доступы (подставлены на экране входа автоматически): **user** `elin@hqrtm.se` / `demo1234`,
> **admin** `admin@hqrtm.se` / `admin1234`. Учётки заданы в `HQRTM-Demo/app/data.jsx` (`DEMO_CREDS`).
> Модульная версия (`HQRTM-Demo/index.html`) грузит `app/*.jsx` через Babel → **работает только по HTTP**
> (GitHub Pages / локальный сервер), не по `file://`. Device-снапшоты — самодостаточны, открываются как файл.

**Мы находимся в начале Фазы 1** (слой данных MongoDB). Фаза 0 завершена.

---

## 4. Целевая структура репозитория (создавать по мере работы)

Из Roadmap §2. Каждый процесс — отдельный контейнер в docker-compose.

```
hqrtm/
├── README.md  COMPLIANCE.md  LICENSE  CONTRIBUTING.md
├── .gitignore  .env.example  docker-compose.yml
├── pyproject.toml / requirements.txt
│
├── poller/        # async-воркер: main.py, homeq_adapter.py, detector.py, matcher.py, dispatcher.py, config.py
├── bot/           # Telegram (aiogram): main.py, handlers.py
├── web/           # Flask: app.py, config.py, auth/, api/, sse/, templates/, static/
├── shared/        # db.py (MongoDB + индексы), models.py (pydantic-схемы)
├── frontend-build/# Tailwind/Bootstrap сборка
├── demo/          # статика для GitHub Pages (index.html, assets/, mock-data.js)
├── tests/         # unit / integration / e2e
└── .github/workflows/  # ci.yml, deploy-pages.yml, deploy-vps.yml
```

**Архитектурный принцип №1:** Flask синхронный (WSGI), поэтому высокочастотный опрос 24/7
**нельзя** держать в обработчиках Flask. Поллер — **отдельный долгоживущий asyncio-процесс**.
Flask отвечает только за API и веб. Связь между ними — **через MongoDB** (поллер пишет,
Flask читает + слушает Change Stream).

---

## 5. Модель данных (MongoDB, из Roadmap §3)

Коллекции: `users`, `filters`, `listings`, `notifications`, `seen_listings`, `audit_log`.

Реализовано в Фазе 1: `shared/models.py` (pydantic-схемы всех коллекций, StrEnum для source/type/
status), `shared/db.py` (`ensure_indexes()` + имена коллекций `COLL_*` + CLI `python -m shared.db`).

Критичные инварианты (соблюдать всегда):
- **Уникум объявления — составной `(source, external_id)`** (мульти-source; уточняет DB-001).
  Индекс `uniq_source_extid`. Тот же `external_id` на разных площадках — это разные объявления.
- **TTL-индекс `seen_listings.seen_at`** (~24 ч, `seen_ttl_hours`) → дедуп без Redis (DB-002).
- **TTL-индекс `listings.fetched_at`** (~7 дней) → авто-очистка (DB-003).
- **Пароли — только хэш** (Argon2/bcrypt), секреты — никогда в открытом виде (DB-004).
- **`notifications.latency_ms`** (publish → delivered) пишется для SLA-отчётности (DB-005).
- **MongoDB в режиме replica set** (минимум single-node RS) — обязательно для Change Streams (DB-006).

---

## 6. Решения (часть закрыта 2026-06-07)

**✅ Принято:**
- **Python 3.12** (venv пересоздан). **MongoDB — Atlas free-tier** (MONGO_URI в `.env`). **Лицензия — MIT**.

**❓ Ещё открыто — спрашивай, не выбирай молча:**
1. **HomeQ:** ✅ официальное API подтверждено (Core API, контракт сверен 2026-06-07 — см.
   `COMPLIANCE.md` и `poller/sources/homeq.py`). **Остаётся блокером:** получить учётку/ключ
   интеграции из landlord-портала + финально подтвердить ToS read-доступа для consumer-сервиса
   (действие владельца). Адаптер написан и протестирован, но `enabled=False` до этого.
2. ✅ **Frontend CSS: Tailwind** (решено 2026-06-07). Сейчас — Play CDN (прототип); production-сборка
   в `frontend-build/` (Tailwind CLI, см. README там) — переезд в полировке/Фазе 8.
3. ✅ **Язык UI — шведский (приоритетный)**, продукт для шведского рынка (решено 2026-06-07).
   Английский — вторичный (i18n-архитектура под добавление). ВЕСЬ текст интерфейса писать
   по-шведски (Logga in, Flöde, Filter, Aviseringar, Konto …); строки — готовить под i18n.
4. Монетизация/тарифы и админ-панель сейчас? (по умолчанию — нет; в демо админка есть как UI).
5. Ожидаемое число пользователей (влияет на выбор VPS) — к Фазе 10.

---

## 7. Roadmap — где мы и что дальше

Полный план в Roadmap §11. Краткая карта фаз и вех:

- **Фаза 0** — ✅ ГОТОВО: репозиторий, структура, окружение, pre-commit, CI.
- **Фаза 1** — ✅ ГОТОВО (код, на ветке `feature/phase1-data-layer`): `shared/models.py`,
  `shared/db.py` (`ensure_indexes`), мульти-source каркас `poller/sources/`. Тесты 22 passed.
  Осталось: прогнать `python -m shared.db` на реальном Atlas (нужен MONGO_URI от владельца).
- **Фаза 2** — 🟡 ЯДРО ГОТОВО (M1): `poller/detector.py` (FCFS vs очередь), `poller/dedup.py`
  (seen_listings), `poller/engine.py` (дедуп→детекция→отсев→upsert), `poller/main.py` (async-цикл,
  адаптивная частота HOT_HOURS, backoff). Тесты 58 passed. **Реальные адаптеры выключены**
  (`enabled=False`) — ждут API-доступа/ToS. Ресёрч ToS зафиксирован в `COMPLIANCE.md`:
  **HomeQ/Qasa имеют официальный Core API** (`docs-core.homeq.se`, JWT + Card Search + webhooks) —
  приоритетный путь; Blocket/Bostad Direkt/Samtrygg — нужен партнёрский доступ/проверка. **Действие
  владельца:** запросить API-ключ HomeQ/Qasa.
  **Реальный HomeQ-адаптер реализован** (`poller/sources/homeq.py`: auth `/api/v2/tokens/` JWT +
  Card Search `/api/v3/cards/` FCFS-only + нормализация + backoff на 429/5xx). **Матчинг готов**
  (`poller/matcher.py` + `engine.enqueue_notifications` → queued-уведомления, идемпотентно;
  оживляет веб-ленту/SSE без Telegram). Ветка `feature/phase2-homeq-adapter`, **80 passed**.
  Остаётся: включение адаптера `enabled=True` (учётка + ToS) и доставка в Telegram (Фаза 3).
- **Фаза 3** — Telegram → **веха M2** (тест-уведомления со ссылкой приходят).
- **Фаза 4** — ✅ ГОТОВО: auth (register/login/refresh, Argon2, JWT), rate-limit, CRUD `/api/filters`,
  `/api/me` (GDPR), `/api/listings` (matched + пагинация), `/api/notifications` (пагинация),
  `/api/telegram/link|status`, OpenAPI (`/openapi.json`) + Swagger UI (`/apidocs`). Тесты 39 passed.
- **Фаза 5** — 🚧 В РАБОТЕ: Jinja2 + Tailwind (Play CDN) + Vanilla JS. Готово: страницы
  landing/login/register, кабинет (дашборд-лента, фильтры CRUD, уведомления, настройки+GDPR),
  JS-клиент `web/static/js/api.js` (токены, auto-refresh, guard), роль user/admin в навигации.
  Маршруты — `web/views.py`. Осталось: i18n (sv/en), SSE-лента (Фаза 6), админ-UI, production Tailwind build.
- **Фаза 6** — ✅ ГОТОВО: SSE + Change Streams. `web/sse/` (broker pub/sub + watcher Change Stream
  `notifications` + эндпоинт `/sse/feed`, auth по `?token=`). Дашборд: `EventSource` с дедупом,
  авто-reconnect, индикатор live, fallback на polling. Тесты 51 passed. (Watcher требует replica set;
  при нескольких web-процессах нужен общий backend — Фаза 8/10.)
- **Фаза 7** — GitHub Pages demo.
- **Фаза 8** — устойчивость/безопасность/наблюдаемость.
- **Фаза 9** — тестирование.
- **Фаза 10** — деплой на VPS → **веха M3** (48-часовой прогон).
- **Фаза 11** — документация и сдача.

**Бюджет латентности (цель ≤ 1.5 с):** опрос ~0.5–0.8 с · запрос+парсинг ~0.2–0.3 с ·
детекция+матчинг ~0.05–0.15 с · отправка в Telegram ~0.2–0.4 с. Любое решение взвешивай против него.

---

## 8. Правила работы (соблюдать неукоснительно)

### Безопасность / секреты (репозиторий публичный!)
- **Ни одного секрета в коде или истории git.** Telegram-токен, Mongo URI, JWT-secret —
  только через `.env` (в `.gitignore`) и GitHub Secrets.
- До первого коммита настроить **pre-commit с detect-secrets** (защита public repo).
- Логи — **без PII** (e-mail, telegram_chat_id и т. п. не логировать).
- Пароли — Argon2/bcrypt. TLS на проде.

### Комплаенс (до начала скрейпинга/опроса)
- Проверить ToS HomeQ и `robots.txt`, выводы → `COMPLIANCE.md`. Официальное API в приоритете.
- Этичная нагрузка: один центральный поллер на всех, разумные интервалы, джиттер,
  экспоненциальный backoff, уважение `429/503/Retry-After`, ротация User-Agent.
- GDPR: согласие при регистрации, политика конфиденциальности, право на удаление данных (`DELETE /api/me`).

### Код и качество
- **Python 3.12** (venv: `/usr/local/bin/python3.12`). Установка: `pip install -e ".[dev]"`.
  Скрейпинг-зависимости — отдельный extra: `pip install -e ".[scraper]" && playwright install`.
- Линт/формат: **ruff + black** (конфиг в `pyproject.toml`, строка ≤ 100). Тесты: **pytest**
  (`pytest -q`). Перед коммитом всё проверяет pre-commit; в CI — `ci.yml`.
- Тесты: unit на `detector`/`matcher`, integration с `mongomock` или test-контейнером, e2e на Playwright.
- Парсер HomeQ изолирован в `HomeQAdapter` — при изменении источника правится **только он** (BE-DE-005).
- Интервал опроса — конфигурируемый (`POLL_INTERVAL_MS`), безопасный дефолт, описать в README.
- Идемпотентность: повторный запуск не должен порождать дубли уведомлений.

### Git / процесс
- Ветвление: `main` ← `develop` ← `feature/*`, через PR.
- Коммитить/пушить — **только когда пользователь попросит**.
- Прослеживаемость: при реализации требования ссылайся на его ID (`BE-DE-001`, `FE-FL-003` и т. п.).

### Взаимодействие с пользователем
- Язык общения — **русский** (пользователь пишет по-русски).
- При противоречии в ТЗ — Roadmap главнее; при неоднозначности из §6 — **спрашивай**, не угадывай.

---

## 9. Памятка по сопровождению этого файла

После каждой значимой сессии обновляй два блока ниже. Это позволит следующему ИИ продолжить
без переоткрытия контекста.

### Текущее состояние (обновлять)
- **2026-06-07 (Фаза 2 — Qasa-адаптер):** `poller/sources/qasa.py` — адаптер Qasa через GraphQL
  (`api.qasa.com/graphql`, запрос `homes`), нормализация в `Listing` (+`fcfs`), backoff на 429/5xx,
  обработка GraphQL-errors. ⚠️ **Контракт НЕ верифицирован** (нет офиц. публичного API Qasa) →
  `enabled=False`, перед включением сверить схему + ToS. Общие хелперы `as_float/as_int` вынесены
  в `poller/sources/base.py` (переиспользуются HomeQ+Qasa). **Исправлен латентный баг:**
  `poller/sources/__init__.py` теперь импортирует конкретные адаптеры → `@register` отрабатывает
  на проде (раньше реестр был пуст при `python -m poller.main`). Тесты `tests/test_qasa_adapter.py`
  (9) + обновлён `test_sources.py`. Весь набор **89 passed**, ruff/black зелёные.
- **2026-06-07 (Фаза 2 — матчинг + постановка уведомлений):** `poller/matcher.py` реализован
  (`matches()` — only_fcfs/sources/диапазоны цены-комнат-площади/район-подстрока; `match_users()`
  — грубый отсев активных фильтров в Mongo + точная проверка в Python). `poller/engine.py` расширен:
  `process_new_listings` теперь проставляет `_id` объявления; новая `enqueue_notifications()` —
  матчинг новых FCFS с фильтрами и **идемпотентная** постановка `notifications` (status=queued,
  доставка/latency — Фаза 3). Добавлен уникальный индекс `notifications (user_id, listing_id)`
  (`uniq_user_listing`) в `shared/db.py`. Цикл `poller/main.py` вызывает enqueue после engine.
  Это оживляет веб-ленту `/api/listings?matched` и SSE (Change Stream на notifications) **без Telegram**.
  Тесты `tests/test_matcher.py` (12). Весь набор **80 passed**, ruff/black зелёные.
  Ветка `feature/phase2-homeq-adapter`. ⚠️ Реальный опрос всё ещё ждёт включения адаптера (учётка+ToS).
- **2026-06-07 (Фаза 2 — реальный HomeQ-адаптер):** Контракт HomeQ Core API сверён по докам
  (`docs-core.homeq.se`/`api.homeq.se`) и реализован в `poller/sources/homeq.py`: auth
  `POST /api/v2/tokens/` (JWT, перелогин на 401), Card Search `POST /api/v3/cards/` с
  `first_come_first=true/queue_points=false` (FCFS-only на источнике), нормализация карточки →
  поля `Listing` (+ `fcfs` для детектора), проброс 429/5xx (Retry-After) для backoff цикла.
  Настройки в `shared/config.py` (`homeq_base_url`/`homeq_username`/`homeq_password`/`homeq_fetch_amount`)
  и `.env.example`. Тесты `tests/test_homeq_adapter.py` на `httpx.MockTransport` (auth, search,
  нормализация, перелогин, троттлинг, нет учётки, путь через детектор). Весь набор **68 passed**,
  ruff/black зелёные. Ветка `feature/phase2-homeq-adapter`. ⚠️ Адаптер `enabled=False` — включение
  и реальный опрос за владельцем (учётка из landlord-портала + подтверждение ToS). Дальше после
  включения: Qasa (тот же API), затем Фаза 3 (Telegram-доставка, веха M2).
- **2026-06-07 (Фаза 2 ядро + ToS-ресёрч):** Ядро поллера готово (детектор FCFS, дедуп, engine,
  async-цикл с адаптивной частотой/backoff) — ветка `feature/phase2-poller`, тесты **58 passed**.
  ToS-ресёрч площадок занесён в `COMPLIANCE.md`: **HomeQ/Qasa — официальный Core API** (приоритет),
  остальные — партнёрство/проверка. Адаптеры всё ещё `enabled=False` (нет ключей/подтверждения ToS).
  Реальная интеграция HomeQ API (Card Search/webhooks) — следующий шаг после получения ключа.
  ⚠️ Это техническая сводка, не юр-консультация — решение о включении за владельцем.
- **2026-06-07 (Фаза 6 + CI ожил):** Real-time готов: `web/sse/` (broker + Change Stream watcher +
  `/sse/feed`), дашборд на `EventSource` (дедуп, авто-reconnect, live-индикатор, fallback polling).
  Тесты **51 passed**. CI на GitHub **зелёный** (биллинг разблокирован). Язык UI зафиксирован —
  **шведский приоритетный** (продукт для шведского рынка), английский вторичный (i18n впереди).
  Ветка `feature/phase6-sse`. Дальше: i18n (sv/en), админ-UI, или Фаза 2 (поллер — блок ToS).
- **2026-06-07 (Фаза 5):** Фронтенд на Jinja2 + **Tailwind** (Play CDN) + Vanilla JS.
  `web/views.py` (страницы), `web/templates/*` (base/app_base + landing/login/register/dashboard/
  filters/notifications/settings), `web/static/js/api.js` (клиент: токены в localStorage, auto-refresh,
  guard, toast). Добавлена роль `UserRole` (user/admin) в модель + в `/api/me`; админ-пункт в навигации
  по роли. `frontend-build/` — конфиг для production Tailwind-сборки (пока CDN). Тесты **48 passed**.
  Ветка `feature/phase5-frontend`. Дальше: Wiki (мануалы), затем i18n / SSE (Фаза 6) / админ-UI.
- **2026-06-07 (Фаза 4 завершена):** Все эндпоинты Фазы 4 готовы и влиты в `develop` (запушено).
  Добавлены: `/api/listings` (matched + пагинация), `/api/notifications` (пагинация),
  `/api/telegram/link|status`, OpenAPI (`web/openapi.py` → `/openapi.json`, Swagger UI `/apidocs`).
  Пагинация: `?page=&limit=` (limit ≤ 100). Тесты **39 passed**, ruff/black зелёные.
  **Дальше на выбор:** Фаза 5 (Jinja2-фронтенд поверх API) или Фаза 2 (поллер, нужен ToS площадок).
- **2026-06-07 (Фаза 4 ядро):** Ветка `feature/phase4-api-auth` (от `develop`). Реализовано ядро web:
  `shared/security.py` (Argon2 + JWT), `web/extensions.py` (limiter), `web/db.py` (DI БД + serialize),
  `web/deps.py` (`require_auth`), blueprints `web/auth/routes.py` (register/login/refresh) и
  `web/api/routes.py` (CRUD filters + /me GDPR). Фабрика `create_app(db=, testing=)`. Тесты: **34 passed**
  (auth, filters CRUD, изоляция пользователей, GDPR-удаление). Площадки в scope: HomeQ, Qasa, Blocket,
  Bostad Direkt, Samtrygg (COMPLIANCE.md). Фаза 1 влита в `develop` и запушена.
  ⚠️ flask-limiter в dev использует in-memory storage (для мульти-процесса нужен backend; Фаза 8/10).
- **2026-06-07 (ещё поздн.):** **Фаза 1 готова** на ветке `feature/phase1-data-layer` (от `develop`).
  `shared/models.py` (все коллекции, мульти-source, StrEnum), `shared/db.py` (`ensure_indexes`,
  составной уникум `(source, external_id)`, TTL), мульти-source каркас `poller/sources/`
  (`SourceAdapter` + реестр + HomeQ-стаб, все `enabled=False`). Добавлен `email-validator`.
  Тесты: 22 passed (models, indexes на mongomock, registry). **Pivot:** проект → all-in-one
  агрегатор шведских площадок. `develop` запушен на GitHub (Фаза 0). ⚠️ GitHub Actions заблокирован
  (биллинг аккаунта) — CI не запускается, но конфиг корректен; локально зелёно.
- **2026-06-07 (поздн.):** **Фаза 0 завершена** на ветке `develop`. Каркас: `pyproject.toml`,
  venv 3.12, пакеты `shared/web/poller/bot` (заглушки с TODO по фазам), `tests/` (10 passed),
  pre-commit (ruff/black/detect-secrets + baseline), CI `ci.yml`, README/COMPLIANCE/CONTRIBUTING/LICENSE.
  `web/app.py` → `/health`. Шаблонный `main.py` удалён. **Дальше: Фаза 1** (MongoDB: `shared/db.py`
  ensure_indexes + `shared/models.py`). Для Фазы 2 нужен ToS HomeQ (§6 п.1 — блокер).
- **2026-06-07:** Создан CLAUDE.md, git/Pages, demo опубликовано (alshfu.github.io/HQRTM/).

### Журнал ключевых решений (дописывать, не переписывать)
- **2026-06-07:** Стек: **Python 3.12**, **MongoDB Atlas free-tier**, лицензия **MIT**.
  Зависимости и tooling — в `pyproject.toml` (`[project]` + `[project.optional-dependencies]`).
  `docker-compose` отложен на Фазу 10 (Atlas для dev, локальный Docker не требуется).
- **2026-06-07:** **Pivot на мульти-source агрегатор** (по предложению владельца). Источник —
  через адаптеры `poller/sources/` (`SourceAdapter` + реестр). Уникум объявления стал
  `(source, external_id)`. Площадки-кандидаты в `COMPLIANCE.md`; финальный набор — за владельцем.
  ToS проверяется per-source, адаптер включается только после этого.
- **2026-06-07:** Каноническим стеком признан Roadmap (Flask + MongoDB + SSE + Vanilla JS).
  Документы Backend/Frontend ToR — источники требований, но их технологии (FastAPI/Postgres/Redis/React)
  не используются.
- **2026-06-07:** Репозиторий — **public** (по GH-001), имя `HQRTM`, аккаунт `alshfu`.
  GitHub Pages отдаётся из ветки `main` / корень; `index.html` в корне = витрина, демо лежит в
  `HQRTM-Demo/`. При смене схемы Pages (например, на `/docs` или `gh-pages`) — обновить пути и этот пункт.
