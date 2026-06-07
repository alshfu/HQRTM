# Roadmap и Changelog

Полный план — `HQRTM_ToR_Flask_MongoDB_Roadmap.md` (§11). Актуальный статус — `CLAUDE.md`.

## Прогресс по фазам
| Фаза | Тема | Статус |
|---|---|---|
| 0 | Подготовка (репо, окружение, tooling, CI) | ✅ |
| 1 | Слой данных MongoDB + мульти-source каркас | ✅ |
| 2 | Поллер: детекция FCFS + адаптеры + матчинг (M1) | ✅ код готов; адаптеры `enabled=False` (ждут ключ/ToS) |
| 3 | Telegram-бот (M2) | ⏳ |
| 4 | Flask API + Auth | ✅ |
| 5 | Frontend (Jinja2 + Tailwind + Vanilla JS) + i18n + админ-UI | ✅ |
| 6 | Real-time (SSE + Change Streams) | ✅ |
| 7 | GitHub Pages demo | ✅ (demo опубликовано) |
| 8 | Устойчивость, безопасность, наблюдаемость | ⏳ |
| 9 | Тестирование | ⏳ (юнит/интеграция идут параллельно, 110 passed) |
| 10 | Деплой на VPS (M3) | ⏳ |
| 11 | Документация и сдача | 🚧 (эта Wiki) |

## Changelog (кратко)
- **2026-06-07** — Фаза 0: каркас, окружение, pre-commit, CI.
- **2026-06-07** — Фаза 1: модели, индексы, мульти-source адаптеры.
- **2026-06-07** — Pivot: all-in-one агрегатор шведских площадок.
- **2026-06-07** — Фаза 4: auth (JWT+Argon2), фильтры, листинги, уведомления, Telegram-link, OpenAPI.
- **2026-06-07** — Фаза 6: real-time (SSE + Change Streams), дашборд на `EventSource`.
- **2026-06-07** — Фаза 2: реальный HomeQ-адаптер (Core API), Qasa-адаптер (GraphQL, не верифицирован),
  матчинг фильтров → идемпотентная постановка уведомлений. Адаптеры `enabled=False`.
- **2026-06-07** — Фаза 5: фронтенд (Tailwind + Vanilla JS), роли user/admin, **i18n (sv/en)**,
  **админ-панель** (`/api/admin/*`, `/app/admin`), **production Tailwind-сборка**. → **v0.5.0**

## Известные внешние блокеры
- Поллер: реальный опрос площадок ждёт включения адаптеров (`enabled=True`) — нужны
  API-ключ/доступ HomeQ/Qasa и подтверждение ToS (решение владельца, см. [Compliance](Compliance)).
