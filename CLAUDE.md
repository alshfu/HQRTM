# CLAUDE.md — руководство для ИИ-ассистента по проекту HQRTM

> Этот файл — точка входа для любого ИИ-ассистента (Claude Code и др.), работающего над проектом.
> Читай его **первым**, до любых действий. Поддерживай его в актуальном состоянии: после
> значимых решений и изменений — обновляй разделы «Текущее состояние» и «Журнал решений» внизу.

---

## 1. Что это за проект

**HQRTM (HomeQ Real-Time Monitor)** — сервис, который круглосуточно мониторит публикации на
платформе **HomeQ**, мгновенно выделяет объявления типа **«Först till kvarn» (FCFS** — «первый
успел, первый получил»), отсеивает «очередные» (queue-объекты), сопоставляет с фильтрами
пользователей и доставляет уведомление со ссылкой в **Telegram за ≤ 1.5 секунды**. Веб-кабинет
позволяет пользователю самому настраивать фильтры, привязывать Telegram и видеть живую ленту.

**Вне scope (важно):** бот **не** логинится в аккаунт HomeQ и **не** подаёт заявки — только уведомляет.

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

Критичные инварианты (соблюдать всегда):
- **`listings.external_id` — UNIQUE-индекс** → каждое объявление обрабатывается ровно один раз (DB-001).
- **TTL-индекс `seen_listings.seen_at`** (~24 ч) → дедуп без Redis (DB-002).
- **TTL-индекс `listings.fetched_at`** (~7 дней) → авто-очистка (DB-003).
- **Пароли — только хэш** (Argon2/bcrypt), секреты — никогда в открытом виде (DB-004).
- **`notifications.latency_ms`** (publish → delivered) пишется для SLA-отчётности (DB-005).
- **MongoDB в режиме replica set** (минимум single-node RS) — обязательно для Change Streams (DB-006).

---

## 6. Решения (часть закрыта 2026-06-07)

**✅ Принято:**
- **Python 3.12** (venv пересоздан). **MongoDB — Atlas free-tier** (MONGO_URI в `.env`). **Лицензия — MIT**.

**❓ Ещё открыто — спрашивай, не выбирай молча:**
1. **HomeQ:** есть ли официальное/партнёрское API? Что разрешает ToS + `robots.txt`?
   (Скрейпинг — только fallback. Зафиксировать в `COMPLIANCE.md` **до Фазы 2**.) — БЛОКЕР Фазы 2.
2. **Frontend CSS:** Tailwind или Bootstrap 5? (Roadmap рекомендует Tailwind.) — нужно к Фазе 5.
3. **Языки UI на старте** (швед./англ.; в демо уже sv+en).
4. Монетизация/тарифы и админ-панель сейчас? (по умолчанию — нет; в демо админка есть как UI).
5. Ожидаемое число пользователей (влияет на выбор VPS) — к Фазе 10.

---

## 7. Roadmap — где мы и что дальше

Полный план в Roadmap §11. Краткая карта фаз и вех:

- **Фаза 0** — ✅ ГОТОВО: репозиторий, структура, окружение, pre-commit, CI.
- **Фаза 1** — слой данных: MongoDB как RS, `shared/db.py` + индексы, `shared/models.py` (pydantic). ← **МЫ ЗДЕСЬ**
- **Фаза 2** — поллер/PoC → **веха M1** (FCFS детектируется, очередные отсекаются).
- **Фаза 3** — Telegram → **веха M2** (тест-уведомления со ссылкой приходят).
- **Фаза 4** — Flask API + Auth (JWT/сессии, CRUD фильтров, OpenAPI).
- **Фаза 5** — Frontend (Jinja2 + Tailwind/Bootstrap + Vanilla JS).
- **Фаза 6** — Real-time (SSE + Change Streams).
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
- **2026-06-07:** Каноническим стеком признан Roadmap (Flask + MongoDB + SSE + Vanilla JS).
  Документы Backend/Frontend ToR — источники требований, но их технологии (FastAPI/Postgres/Redis/React)
  не используются.
- **2026-06-07:** Репозиторий — **public** (по GH-001), имя `HQRTM`, аккаунт `alshfu`.
  GitHub Pages отдаётся из ветки `main` / корень; `index.html` в корне = витрина, демо лежит в
  `HQRTM-Demo/`. При смене схемы Pages (например, на `/docs` или `gh-pages`) — обновить пути и этот пункт.
