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
├── index.html                           # витрина GitHub Pages (выбор устройства + баннер demo)
├── HQRTM-Demo/                          # прототипы UI: HQRTM-{Desktop,Tablet,Mobile}.html (self-contained)
├── .gitignore                           # защита public repo (.env, .venv, .idea, ...)
├── main.py                              # шаблон PyCharm («Hi, PyCharm») — заглушка, будет удалён/заменён
├── .venv/  (ignored)                    # Python 3.14 (NB: ТЗ требует 3.12+, см. §8)
└── .idea/  (ignored)                    # настройки PyCharm
```

**Готово:**
- ✅ Git-репозиторий инициализирован (ветка `main`).
- ✅ GitHub: **https://github.com/alshfu/HQRTM** (public, аккаунт `alshfu`).
- ✅ GitHub Pages включён (source: `main` / корень): **https://alshfu.github.io/HQRTM/** — demo отдаётся (HTTP 200).

**Ещё НЕ сделано (всё впереди):** ветки `develop`/`feature/*`, структуры каталогов
(`poller/`, `bot/`, `web/`, `shared/`) нет, зависимостей нет, MongoDB не настроена,
`.env.example`/`README`/`COMPLIANCE.md`/pre-commit/CI отсутствуют.

> ⚠️ Демо в `HQRTM-Demo/` — это **дизайн-прототипы на чистом HTML/CSS/JS**, не итоговый фронтенд.
> Боевой фронтенд по канону — Jinja2 + Tailwind/Bootstrap внутри `web/` (Фаза 5). Прототипы — референс UI.

**Мы находимся в Фазе 0** (частично выполнена: репо + Pages; осталось остальное по списку выше).

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

## 6. Незакрытые решения (спросить пользователя перед реализацией)

Не выбирай молча — это решения уровня владельца проекта:

1. **HomeQ:** есть ли официальное/партнёрское API? Что разрешает ToS + `robots.txt`?
   (Скрейпинг — только fallback и только если не противоречит ToS. Зафиксировать в `COMPLIANCE.md`.)
2. **Frontend CSS:** Tailwind или Bootstrap 5? (Roadmap рекомендует Tailwind для кастомного вида.)
3. **MongoDB:** self-hosted (настройка RS вручную) или Atlas free-tier (RS из коробки)?
4. **Языки UI на старте** (швед./англ./др.).
5. Нужны ли монетизация/тарифы и админ-панель уже сейчас (по умолчанию — нет, опционально).
6. Ожидаемое число пользователей (влияет на выбор VPS).

---

## 7. Roadmap — где мы и что дальше

Полный план в Roadmap §11. Краткая карта фаз и вех:

- **Фаза 0** — подготовка: репозиторий, структура, `.env`/`.gitignore`, pre-commit (ruff/black + **detect-secrets**), CI. ← **МЫ ЗДЕСЬ**
- **Фаза 1** — слой данных: MongoDB как RS, `shared/db.py` + индексы, `shared/models.py` (pydantic).
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
- **Python 3.12+** по ТЗ. ⚠️ В `.venv` сейчас Python **3.14** — проверь совместимость
  библиотек (PyMongo/Motor/aiogram/Flask) или пересоздай venv на 3.12, если будут проблемы.
- Линт/формат: **ruff + black**. Тесты: pytest (unit на `detector`/`matcher`, integration с
  `mongomock` или test-контейнером, e2e на Playwright).
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
- **2026-06-07:** Создан CLAUDE.md. Инициализирован git (`main`), создан public-репо
  github.com/alshfu/HQRTM, включён GitHub Pages → alshfu.github.io/HQRTM/ (demo отдаётся, 200).
  Закоммичены: 3 ТЗ, CLAUDE.md, HQRTM-Demo/, index.html (витрина), .gitignore, main.py.
  Кода приложения (poller/web/bot/shared) ещё нет. Открытые вопросы §6 — не закрыты.

### Журнал ключевых решений (дописывать, не переписывать)
- **2026-06-07:** Каноническим стеком признан Roadmap (Flask + MongoDB + SSE + Vanilla JS).
  Документы Backend/Frontend ToR — источники требований, но их технологии (FastAPI/Postgres/Redis/React)
  не используются.
- **2026-06-07:** Репозиторий — **public** (по GH-001), имя `HQRTM`, аккаунт `alshfu`.
  GitHub Pages отдаётся из ветки `main` / корень; `index.html` в корне = витрина, демо лежит в
  `HQRTM-Demo/`. При смене схемы Pages (например, на `/docs` или `gh-pages`) — обновить пути и этот пункт.
