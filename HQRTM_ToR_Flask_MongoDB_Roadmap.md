# Техническое задание + Roadmap
## Проект: HomeQ Real-Time Monitor (HQRTM)
### Стек: Flask · MongoDB · HTML/CSS/JS · Tailwind CSS / Bootstrap · GitHub (Public Repo + Pages + Wiki)

---

## 0. Введение

### 0.1 Назначение
Сервис круглосуточно отслеживает публикации HomeQ, мгновенно выделяет объявления типа «Först till kvarn» (FCFS — первый успел, первый получил), отсеивает очередные, сопоставляет их с фильтрами пользователей и доставляет уведомление со ссылкой в Telegram в пределах ≤ 1.5 с. Веб-интерфейс (личный кабинет) даёт пользователю самостоятельно настраивать фильтры, привязывать Telegram и видеть живую ленту совпадений.

### 0.2 Зафиксированный стек
| Слой | Технология |
|---|---|
| Backend API + Web | **Flask 3.x** (Python 3.12+), Jinja2 шаблоны |
| Поллер / воркер | **Отдельный asyncio-процесс**: `httpx` + `asyncio` (+ `Playwright` как fallback) |
| Telegram | `aiogram` (async) |
| База данных | **MongoDB** (PyMongo для Flask, Motor для async-воркера) |
| Real-time | **MongoDB Change Streams + SSE** (или Flask-SocketIO) |
| Frontend стили | **Tailwind CSS** или **Bootstrap 5** (выбор — §7) |
| Frontend логика | Vanilla **JavaScript** (`fetch`, `EventSource`) |
| Репозиторий | **GitHub — public** |
| Demo / витрина | **GitHub Pages** (статическая сборка с мок-данными) |
| Документация | **GitHub Wiki** |
| CI/CD | GitHub Actions |
| Контейнеризация / деплой | Docker + docker-compose на VPS, Nginx + TLS |

### 0.3 Глоссарий
| Термин | Значение |
|---|---|
| **FCFS / «Först till kvarn»** | Объявление «первый успел — первый получил» (целевой объект). |
| **Queue-объект** | Очередная квартира (по баллам/времени) — **исключается** фильтром. |
| **Poller / Monitoring Engine** | Отдельный async-процесс, опрашивающий HomeQ. |
| **Dispatcher** | Рассылка уведомлений (Telegram). |
| **Change Stream** | Механизм MongoDB для реакции на изменения в коллекциях в реальном времени. |
| **SSE** | Server-Sent Events — однонаправленный поток сервер → браузер. |

### 0.4 Технические оговорки по стеку (важно!)
1. **Flask синхронный (WSGI).** Высокочастотный опрос 24/7 нельзя держать в обработчиках Flask. Поллер — **отдельный долгоживущий процесс** на `asyncio`. Flask отвечает только за API и веб-интерфейс. Связь — через MongoDB.
2. **GitHub Pages — только статика.** Живой Flask туда не деплоится. На Pages публикуется **статическая demo-сборка фронтенда с мок-данными** (витрина + документация); рабочий бэкенд — на VPS.
3. **Public Repo ⇒ нет секретов в коде.** Telegram-токен, Mongo URI, JWT-secret и т. п. — **только** через `.env` (в `.gitignore`) и **GitHub Secrets**. Ни одного секрета в истории коммитов.
4. **Real-time без Redis.** Используем MongoDB Change Streams (требуют MongoDB в режиме replica set; в MongoDB Atlas включён по умолчанию, для self-hosted — настроить).

### 0.5 Комплаенс (обязательно до старта)
- **ToS HomeQ + `robots.txt`:** проверить, зафиксировать в `COMPLIANCE.md`. Официальное API — в приоритете; скрейпинг — fallback и только если не противоречит ToS.
- **GDPR (ЕС):** правовое основание, политика конфиденциальности, право на удаление данных, шифрование секретов, журнал согласий.
- **Этичная нагрузка:** один центральный поллер на всех, разумные интервалы, backoff, реакция на `429/503`.
- **Вне scope:** бот не логинится в аккаунт HomeQ и не подаёт заявки — только уведомляет.

---

## 1. Архитектура решения

```
                          ┌──────────────────────────┐
                          │       HomeQ (источник)    │
                          └─────────────▲─────────────┘
                                        │ опрос (1 раз на всех)
        ┌───────────────────────────────┴───────────────────────────────┐
        │              ПОЛЛЕР (asyncio-процесс, отдельный контейнер)       │
        │   HomeQAdapter → FCFS Detector → Filter Matcher → Dispatcher     │
        └───────┬───────────────────────────────────────────┬────────────┘
                │ запись listings / notifications            │ Telegram
        ┌───────▼────────────┐                       ┌───────▼────────────┐
        │      MongoDB        │◄──── Change Stream ───│   Telegram Bot     │
        │ users / filters /   │                       │   (aiogram)        │
        │ listings / notif.   │                       └────────────────────┘
        └───────▲────────────┘
                │ PyMongo
        ┌───────┴────────────────────────────────┐
        │        FLASK (API + Web, Jinja2)         │──── SSE/SocketIO ───► Браузер
        │  auth · filters · listings · /ws/feed    │                       (live feed)
        └──────────────────────────────────────────┘
```

**Процессы (раздельные контейнеры в docker-compose):**
1. `poller` — asyncio: опрос, детекция FCFS, матчинг, постановка уведомлений.
2. `bot` — Telegram-бот (может быть в составе `poller` или отдельно).
3. `web` — Flask (API + веб-интерфейс + SSE).
4. `mongo` — MongoDB (replica set для Change Streams).

> Почему поллер отдельно: низкая латентность и непрерывный async-цикл несовместимы с request-response моделью Flask. Разделение также позволяет масштабировать веб и поллер независимо.

---

## 2. Структура репозитория

```
hqrtm/
├── README.md                  # Quickstart, запуск/остановка, настройка частоты
├── COMPLIANCE.md              # Выводы по ToS HomeQ + GDPR
├── LICENSE
├── CONTRIBUTING.md
├── .gitignore                 # .env, __pycache__, node_modules, dist/ ...
├── .env.example               # Шаблон переменных (без значений секретов)
├── docker-compose.yml
├── pyproject.toml / requirements.txt
│
├── poller/                    # Async-воркер
│   ├── main.py                # Точка входа (asyncio loop)
│   ├── homeq_adapter.py       # Получение + нормализация данных HomeQ
│   ├── detector.py            # Логика FCFS vs очередь
│   ├── matcher.py             # Матчинг с фильтрами
│   ├── dispatcher.py          # Постановка/отправка уведомлений
│   └── config.py
│
├── bot/                       # Telegram-бот (aiogram)
│   ├── main.py
│   └── handlers.py            # /start, привязка, тест-уведомление
│
├── web/                       # Flask
│   ├── app.py                 # Фабрика приложения, blueprints
│   ├── config.py
│   ├── auth/                  # Регистрация/логин (blueprint)
│   ├── api/                   # REST endpoints (blueprint)
│   ├── sse/                   # SSE / Change Stream listener
│   ├── templates/             # Jinja2 (base.html, dashboard.html, ...)
│   └── static/                # Скомпилированный CSS, JS, иконки
│
├── shared/
│   ├── db.py                  # Подключение к MongoDB, индексы
│   └── models.py              # Схемы/валидация документов (pydantic)
│
├── frontend-build/            # Tailwind/Bootstrap сборка (input.css, config)
│
├── demo/                      # Статическая сборка для GitHub Pages (мок-данные)
│   ├── index.html
│   ├── assets/
│   └── mock-data.js
│
├── tests/                     # unit / integration / e2e
└── .github/
    └── workflows/             # ci.yml, deploy-pages.yml, deploy-vps.yml
```

---

## 3. Модель данных MongoDB

**Коллекции и ключевые индексы:**

```javascript
// users
{ _id, email (unique idx), password_hash, telegram_chat_id,
  link_code, status, locale, consent_at, created_at }

// filters
{ _id, user_id (idx), name, city, district, rent_min, rent_max,
  rooms_min, rooms_max, area_min, area_max, only_fcfs:true, is_active, created_at }

// listings
{ _id, external_id (UNIQUE idx), title, address, district, rooms,
  area_m2, rent, listing_type, url, published_at, fetched_at (TTL idx, напр. 7 дней) }

// notifications
{ _id, user_id (idx), listing_id, channel:"telegram",
  status, sent_at, latency_ms, error }

// seen_listings   (дедупликация)
{ _id: external_id, seen_at (TTL idx, напр. 24 ч) }

// audit_log
{ _id, actor, action, payload, created_at }
```

**Требования к данным:**
| ID | Требование |
|---|---|
| DB-001 | `external_id` уникален — гарантирует, что объявление обрабатывается один раз. |
| DB-002 | TTL-индекс на `seen_listings.seen_at` авто-чистит старые записи дедупа (вместо Redis). |
| DB-003 | TTL-индекс на `listings.fetched_at` для авто-очистки устаревших объявлений. |
| DB-004 | Пароли — только хэш (Argon2/bcrypt); секреты не хранятся в открытом виде. |
| DB-005 | `notifications.latency_ms` (publish → delivered) пишется для отчётности по SLA. |
| DB-006 | MongoDB запущен как replica set (минимум single-node RS) для работы Change Streams. |

---

## 4. Функциональные требования

### 4.1 Поллер / Monitoring Engine
| ID | Требование |
|---|---|
| BE-DE-001 | Получение объявлений HomeQ через API (приоритет) или скрейпинг (fallback, `Playwright`). |
| BE-DE-002 | Опрос **централизован** — один раз за цикл, независимо от числа пользователей. |
| BE-DE-003 | Интервал опроса конфигурируется (`POLL_INTERVAL_MS`), безопасный дефолт; описать в README. |
| BE-DE-004 | Адаптивная частота: учащение в «горячие» часы, замедление ночью. |
| BE-DE-005 | Парсер изолирован в `HomeQAdapter`; при изменении источника правится только он. |
| BE-DE-006 | Нормализация в единую модель документа `listings`. |

### 4.2 Детекция и фильтрация
| ID | Требование |
|---|---|
| BE-FL-001 | Детекция FCFS vs очередь (`detector.py`), покрыта тестами. |
| BE-FL-002 | Дальше проходят **только FCFS**; очередные отсекаются сразу. |
| BE-FL-003 | Дедупликация через `seen_listings` + unique-индекс. |
| BE-FL-004 | Матчинг с фильтрами: город/район, цена, комнаты, площадь, `only_fcfs`. |
| BE-FL-005 | Эффективный матчинг (MongoDB-запрос с индексами), без превышения бюджета латентности. |

### 4.3 Уведомления (Telegram)
| ID | Требование |
|---|---|
| BE-NT-001 | Сообщение: заголовок, район, цена, комнаты, площадь + **прямая ссылка** на объявление. |
| BE-NT-002 | Параллельная рассылка всем совпавшим пользователям (async). |
| BE-NT-003 | Троттлинг под лимиты Telegram Bot API. |
| BE-NT-004 | Повторные попытки с backoff; статусы пишутся в `notifications`. |
| BE-NT-005 | Привязка через deep-link/код подтверждения (используется и веб-кабинетом). |

### 4.4 Flask API
| ID | Endpoint | Назначение |
|---|---|---|
| BE-API-001 | `POST /auth/register`, `/auth/login`, `/auth/refresh` | Регистрация/вход (JWT). |
| BE-API-002 | `GET/POST/PUT/DELETE /api/filters` | CRUD фильтров. |
| BE-API-003 | `GET /api/listings?matched=true` | Лента совпавших объявлений. |
| BE-API-004 | `GET /api/notifications` | История (пагинация). |
| BE-API-005 | `POST /api/telegram/link`, `GET /api/telegram/status` | Привязка/статус Telegram. |
| BE-API-006 | `GET/PUT/DELETE /api/me` | Профиль; удаление аккаунта и данных (GDPR). |
| BE-API-007 | `GET /sse/feed` | SSE-поток новых совпадений. |
| BE-API-008 | `GET /health`, `/metrics` | Health-check и метрики. |
| BE-API-009 | — | OpenAPI/Swagger (flasgger / apispec). |

### 4.5 Веб-интерфейс (экраны)
| ID | Экран / требование |
|---|---|
| FE-001 | Landing + регистрация/вход. |
| FE-002 | Онбординг: привязка Telegram (deep-link/код) + создание первого фильтра. |
| FE-003 | Управление фильтрами (CRUD, вкл/выкл, клиентская валидация диапазонов). |
| FE-004 | Дашборд с **живой лентой** совпадений (SSE), карточка + кнопка перехода на HomeQ. |
| FE-005 | История уведомлений (пагинация, фильтрация). |
| FE-006 | Настройки аккаунта: профиль, смена пароля, удаление данных (GDPR). |
| FE-007 | Адаптивность (mobile-first), a11y, локализация (шв./англ.). |
| FE-008 | Состояния загрузки/ошибки/пусто на всех экранах; авто-reconnect SSE. |

---

## 5. Нефункциональные требования + бюджет латентности
| ID | Требование | Цель |
|---|---|---|
| NFR-001 | Латентность publish → доставка | ≤ **1.5 с** (целевая ≤ 1.0 с) |
| NFR-002 | Доступность | ≥ 99.5% / месяц |
| NFR-003 | Пропускная способность рассылки | ≥ сотни/мин без деградации опроса |
| NFR-004 | Масштабируемость | центральный опрос неизменен при росте пользователей |
| NFR-005 | Восстановление | автоперезапуск процессов, без потери дедупа |
| NFR-006 | Безопасность | TLS, хэш паролей, секреты вне репозитория, без PII в логах |

**Бюджет латентности (целевые 1.5 с):** опрос ~0.5–0.8 с · запрос+парсинг ~0.2–0.3 с · детекция+матчинг ~0.05–0.15 с · отправка в Telegram ~0.2–0.4 с.

---

## 6. Frontend: Tailwind CSS vs Bootstrap
| Критерий | Tailwind CSS | Bootstrap 5 |
|---|---|---|
| Подход | Utility-first, кастомный дизайн | Готовые компоненты |
| Скорость старта | Чуть медленнее (нужен build) | Очень быстро (CDN) |
| Уникальность UI | Высокая | Средняя (узнаваемый «бутстрап-вид») |
| Размер бандла | Малый (purge неиспользуемого) | Больше из коробки |
| Кривая входа | Чуть выше | Низкая |

**Рекомендация:** если важен кастомный современный вид и есть время на build-шаг — **Tailwind** (через CLI/PostCSS; для прототипа допустим Play CDN). Если приоритет — скорость и готовые компоненты — **Bootstrap 5** (CDN, минимум настройки). Выбор фиксируется в начале §Roadmap, фаза 5.

**UI-структура:** базовый шаблон `base.html` (шапка/навигация/футер) → наследуемые страницы; общий дизайн-токен (цвета, типографика); компоненты карточки объявления, формы фильтра, тост-уведомлений.

---

## 7. Real-time стратегия
1. Поллер пишет новое совпадение в `notifications`.
2. Flask слушает **Change Stream** коллекции `notifications` (фоновый поток).
3. По событию Flask отправляет данные в браузер через **SSE** (`/sse/feed`), фильтруя по `user_id`.
4. Клиент (`EventSource`) добавляет карточку в ленту без перезагрузки; при разрыве — авто-reconnect.
5. Fallback: если SSE недоступен — периодический `GET /api/listings?matched=true`.

> Альтернатива — Flask-SocketIO (двусторонний канал). SSE проще и достаточен для односторонней ленты.

---

## 8. GitHub: репозиторий, ветки, CI/CD
| ID | Требование |
|---|---|
| GH-001 | **Public** репозиторий; `LICENSE`, `README`, `CONTRIBUTING`, `.gitignore`. |
| GH-002 | Ветвление: `main` (стабильная) ← `develop` ← `feature/*`; PR + ревью. |
| GH-003 | Секреты — **только** в GitHub Secrets и локальном `.env`; `.env` в `.gitignore`. |
| GH-004 | Pre-commit хуки (ruff/black, detect-secrets) — защита от утечки токенов в public repo. |
| GH-005 | CI (`ci.yml`): линт + тесты на каждый PR. |
| GH-006 | CD (`deploy-pages.yml`): сборка demo → GitHub Pages. |
| GH-007 | CD (`deploy-vps.yml`): деплой контейнеров на VPS (по тегу/релизу). |
| GH-008 | Issues + Projects (kanban) для трекинга задач roadmap. |

---

## 9. GitHub Pages: что публикуем
**Только статика** — demo-витрина для стейкхолдеров (живой бэкенд остаётся на VPS):
| ID | Требование |
|---|---|
| GP-001 | Статическая сборка фронтенда из `demo/` с **мок-данными** (`mock-data.js`). |
| GP-002 | Демонстрирует: дашборд, ленту, формы фильтров, экран привязки Telegram — без реального API. |
| GP-003 | Можно добавить страницу-галерею примеров уведомлений (скриншоты). |
| GP-004 | Публикация автоматическая через Actions (ветка `gh-pages` или каталог `/docs`). |
| GP-005 | Ссылка на demo — в `README` и в Wiki. |
| GP-006 | На demo — баннер «Demo с мок-данными, не рабочий сервис». |

---

## 10. GitHub Wiki: структура страниц
| Страница | Содержание |
|---|---|
| **Home** | Обзор проекта, ссылки на ключевые страницы и demo. |
| **Architecture** | Диаграмма, описание процессов (poller/web/bot/mongo). |
| **Setup & Installation** | Локальный запуск: Python, MongoDB (RS), `.env`, frontend-build. |
| **Configuration** | Все переменные окружения, как менять частоту опроса. |
| **Data Model** | Коллекции MongoDB, индексы, примеры документов. |
| **FCFS Detection** | Как определяется «Först till kvarn», граничные случаи. |
| **API Reference** | Эндпоинты, запросы/ответы (со ссылкой на Swagger). |
| **Frontend Guide** | Сборка Tailwind/Bootstrap, структура шаблонов, SSE. |
| **Deployment (VPS)** | Docker, Nginx, TLS, бэкапы, запуск/остановка. |
| **GitHub Pages Demo** | Как собирается и публикуется витрина. |
| **Troubleshooting / FAQ** | Типовые проблемы (источник недоступен, SSE рвётся и т. п.). |
| **Compliance & Legal** | ToS HomeQ, GDPR, ограничения (вне scope). |
| **Roadmap & Changelog** | Прогресс по фазам, история версий. |

---

## 11. ROADMAP — пошаговая реализация
> Чек-листы можно вести прямо в Issues/Projects. Сроки ориентировочные (для 1 разработчика); при команде — параллелится.

### Фаза 0 — Подготовка (≈ 2–3 дня)
- [ ] Создать **public** репозиторий, добавить `LICENSE`, `README`, `.gitignore`, `CONTRIBUTING.md`.
- [ ] Завести структуру каталогов (см. §2).
- [ ] Настроить виртуальное окружение, `requirements.txt`/`pyproject.toml`.
- [ ] Создать `.env.example`; настроить загрузку `.env` (python-dotenv); добавить `.env` в `.gitignore`.
- [ ] Подключить pre-commit (ruff/black + **detect-secrets**) — защита public repo от утечек.
- [ ] Инициализировать **Wiki** скелетом страниц (§10, пока заглушки).
- [ ] Настроить CI `ci.yml` (линт + пустой прогон тестов).
- [ ] Создать GitHub Project (kanban) и перенести шаги roadmap в Issues.

### Фаза 1 — Слой данных MongoDB (≈ 2–3 дня)
- [ ] Поднять MongoDB локально как **replica set** (для Change Streams) и/или завести Atlas free-tier.
- [ ] `shared/db.py`: подключение (PyMongo + Motor), функция создания индексов.
- [ ] Создать коллекции и индексы (unique `external_id`, TTL `seen_listings`, TTL `listings`).
- [ ] `shared/models.py`: pydantic-схемы и валидация документов.
- [ ] Wiki: заполнить **Data Model**.

### Фаза 2 — Поллер / PoC (≈ 1 неделя) → **Веха M1**
- [ ] Исследовать источник HomeQ (API vs скрейпинг), зафиксировать в `COMPLIANCE.md`.
- [ ] `homeq_adapter.py`: получение + нормализация в модель `listings`.
- [ ] `detector.py`: логика FCFS vs очередь + unit-тесты на граничные случаи.
- [ ] Дедупликация через `seen_listings`.
- [ ] `poller/main.py`: async-цикл опроса с backoff и адаптивной частотой.
- [ ] **Проверка M1:** FCFS-объявления стабильно детектируются, очередные отсекаются.
- [ ] Wiki: **FCFS Detection**.

### Фаза 3 — Telegram-интеграция (≈ 4–5 дней) → **Веха M2**
- [ ] Создать бота через BotFather; токен — в `.env`/Secrets (не в коде!).
- [ ] `bot/handlers.py`: `/start`, привязка по deep-link/коду, тест-уведомление.
- [ ] `matcher.py`: матчинг объявления с фильтрами пользователей (MongoDB-запрос).
- [ ] `dispatcher.py`: async-рассылка, троттлинг, retry, запись в `notifications` + `latency_ms`.
- [ ] **Проверка M2:** тестовые уведомления приходят с корректными данными и ссылкой.

### Фаза 4 — Flask API + Auth (≈ 1 неделя)
- [ ] `web/app.py`: фабрика приложения, blueprints, конфиг.
- [ ] Auth: регистрация/логин, хэш паролей (Argon2/bcrypt), JWT (access+refresh) или сессии.
- [ ] Rate-limiting на auth (flask-limiter).
- [ ] CRUD `/api/filters`.
- [ ] `/api/listings`, `/api/notifications` (пагинация).
- [ ] `/api/telegram/link`, `/api/telegram/status`.
- [ ] `/api/me` (GET/PUT/DELETE — удаление данных GDPR).
- [ ] OpenAPI/Swagger (flasgger).
- [ ] Wiki: **API Reference**, **Configuration**.

### Фаза 5 — Frontend (Flask + Tailwind/Bootstrap + JS) (≈ 1.5 недели)
- [ ] **Зафиксировать выбор: Tailwind или Bootstrap**; настроить build (или CDN).
- [ ] `base.html` + дизайн-токены + навигация/футер.
- [ ] Страницы auth (регистрация/вход) с валидацией.
- [ ] Онбординг + UI привязки Telegram (статус, тест-уведомление).
- [ ] UI управления фильтрами (CRUD, вкл/выкл, валидация диапазонов).
- [ ] Дашборд + **живая лента** (SSE/`EventSource`) + карточка объявления.
- [ ] История уведомлений (пагинация, фильтры).
- [ ] Настройки аккаунта (профиль, пароль, удаление данных).
- [ ] Адаптивность (mobile-first), a11y, i18n (шв./англ.), состояния загрузки/ошибки/пусто.
- [ ] Wiki: **Frontend Guide**.

### Фаза 6 — Real-time (SSE + Change Streams) (≈ 3–4 дня)
- [ ] Фоновый слушатель Change Stream коллекции `notifications` в Flask.
- [ ] Эндпоинт `/sse/feed` с фильтрацией по `user_id`.
- [ ] Клиентский `EventSource` + дедуп + авто-reconnect; fallback на polling.
- [ ] Тест разрыва соединения и восстановления.

### Фаза 7 — GitHub Pages demo (≈ 2–3 дня)
- [ ] Собрать статическую версию фронтенда в `demo/` с `mock-data.js`.
- [ ] Добавить баннер «Demo / мок-данные».
- [ ] Настроить `deploy-pages.yml` (Actions → `gh-pages`/`/docs`).
- [ ] Проверить публикацию, добавить ссылку в `README` и Wiki.
- [ ] Wiki: **GitHub Pages Demo**.

### Фаза 8 — Устойчивость, безопасность, наблюдаемость (≈ 4–5 дней)
- [ ] Обработка ошибок + circuit breaker в поллере; реакция на `429/403`.
- [ ] Алерты администратору (Telegram/e-mail) при сбоях источника/рассылок/росте латентности.
- [ ] Anti-blocking в рамках ToS: ротация User-Agent, джиттер интервалов, уважение `Retry-After`.
- [ ] Структурное логирование (без PII), `/health`, `/metrics`.
- [ ] Graceful degradation при изменении разметки HomeQ (алерт, без падения).

### Фаза 9 — Тестирование (≈ 1 неделя)
- [ ] Unit: `detector`, `matcher` (включая граничные случаи).
- [ ] Integration: API + MongoDB (`mongomock` или test-контейнер).
- [ ] Дедупликация и идемпотентность.
- [ ] E2E (Playwright): регистрация → привязка Telegram → создание фильтра → совпадение в ленте.
- [ ] Нагрузочный (locust): рост пользователей при неизменном центральном опросе.
- [ ] Замер реальной латентности на тестовых данных.

### Фаза 10 — Развёртывание на VPS (≈ 4–5 дней) → **Веха M3**
- [ ] Dockerfile-ы для `poller`, `bot`, `web`; `docker-compose.yml` (+ `mongo` как RS).
- [ ] Провизия VPS; Nginx reverse proxy; TLS (Let's Encrypt/certbot).
- [ ] Restart-policy / автоперезапуск процессов.
- [ ] Бэкап MongoDB (`mongodump` по cron).
- [ ] `deploy-vps.yml` (CI/CD деплой по релизу).
- [ ] **48-часовой живой тест-прогон.**
- [ ] Wiki: **Deployment (VPS)**.

### Фаза 11 — Документация и сдача (≈ 2–3 дня)
- [ ] Дозаполнить все страницы Wiki (§10).
- [ ] Финализировать `README` (quickstart, запуск/остановка, настройка частоты).
- [ ] `COMPLIANCE.md`, `LICENSE`, `CONTRIBUTING.md` — финал.
- [ ] Пройти чек-лист приёмки (§14) и Definition of Done (§15).

**Сводный таймлайн (ориентир, 1 разработчик):** ≈ 7–9 недель. M1 — конец фазы 2; M2 — конец фазы 3; M3 — конец фазы 10.

---

## 12. Тестирование (сводно)
Unit (детектор, матчинг) · Integration (API + Mongo) · Дедуп/идемпотентность · E2E (Playwright, полный путь пользователя) · Нагрузочный (locust) · Замер латентности · Тест «поломки источника».

---

## 13. Безопасность и анонимизация (в рамках ToS)
TLS · хэш паролей (Argon2/bcrypt) · секреты вне репозитория (Secrets + `.env`) · detect-secrets в pre-commit · rate-limiting на auth · ротация User-Agent · разумные интервалы и джиттер · уважение `429/Retry-After` · логи без PII.

---

## 14. Поставки и критерии приёмки
**Поставки:**
1. Документированный код в **public** GitHub-репозитории (poller + bot + web).
2. Развёрнутый рабочий сервис на VPS (24/7).
3. **GitHub Pages** — статическая demo-витрина с мок-данными.
4. Полная **GitHub Wiki**.
5. `README` (запуск/остановка/частота), `COMPLIANCE.md`, OpenAPI-документация.

**Критерии приёмки:**
- FCFS детектируются, очередные отсекаются (тесты + реальные данные).
- Уведомление со ссылкой приходит в Telegram; измеренная латентность ≤ 1.5 с.
- Веб-кабинет: полный путь регистрация → Telegram → фильтр → живая лента → история.
- Сервис переживает сетевые сбои и эмуляцию изменения источника без падения.
- Demo опубликовано на Pages, Wiki заполнена, в публичной истории нет секретов.

---

## 15. Риски и Definition of Done
| Риск | Митигация |
|---|---|
| Изменение источника HomeQ | Изолированный адаптер, тесты, алерт + graceful degradation. |
| Блокировка по частоте/IP | Центральный поллер, разумные интервалы, backoff, `429`. |
| Утечка секретов в public repo | `.gitignore`, GitHub Secrets, detect-secrets в pre-commit. |
| Flask-латентность | Поллер — отдельный async-процесс; матчинг по индексам. |
| Change Streams не работают | MongoDB в режиме replica set (Atlas или настройка RS). |
| GitHub Pages ≠ бэкенд | На Pages — только статический demo; рабочий бэкенд на VPS. |
| GDPR-несоответствие | Политика, согласия, удаление данных, шифрование секретов. |

**Definition of Done:** все критерии приёмки выполнены · CI зелёный · мониторинг/алерты + бэкап БД настроены · документация (Wiki/README/COMPLIANCE/OpenAPI) актуальна · 48-часовой прогон без критических инцидентов · в публичной истории нет секретов.

---

## 16. Открытые вопросы (зафиксировать до старта)
1. HomeQ: есть ли официальное/партнёрское API? Что разрешает ToS?
2. Tailwind или Bootstrap — финальный выбор?
3. Ожидаемое число пользователей (нагрузка, выбор VPS)?
4. Нужна ли монетизация/тарифы и админ-панель в этой фазе?
5. MongoDB: self-hosted (настройка replica set) или Atlas?
6. Языки интерфейса на старте (шв./англ./др.)?
