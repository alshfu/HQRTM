# Архитектура

```
        Площадки (HomeQ, Qasa, Blocket, Bostad Direkt, Samtrygg)
                         │ опрос (1 раз на всех)
        ┌────────────────▼─────────────────────────────────────┐
        │  POLLER (asyncio, отдельный процесс)                  │
        │  sources/* (адаптеры) → detector(FCFS) → matcher → dispatcher │
        └───────┬───────────────────────────────────┬──────────┘
                │ listings / notifications           │ Telegram (aiogram)
        ┌───────▼────────────┐               ┌───────▼────────┐
        │      MongoDB        │◄─Change Stream│   Telegram Bot │
        │ users/filters/      │               └────────────────┘
        │ listings/notif/seen │
        └───────▲────────────┘
                │ PyMongo
        ┌───────┴───────────────────────────────┐
        │  FLASK (API + Jinja2 + SSE)            │── SSE ─► Браузер (Tailwind+JS)
        └────────────────────────────────────────┘
```

## Принципы
- **Поллер — отдельный процесс.** Flask синхронный (WSGI); высокочастотный опрос 24/7 несовместим
  с request-response. Связь web↔poller — через MongoDB.
- **Мульти-source.** Каждая площадка — адаптер `SourceAdapter` в `poller/sources/`, регистрируется в
  реестре. Всё нормализуется в коллекцию `listings` с полем `source`. Добавить площадку = новый адаптер,
  ядро поллера не меняется. Включение адаптера (`enabled=True`) — только после проверки ToS.
- **Real-time.** Поллер пишет совпадение → Flask слушает Change Stream `notifications` → отдаёт в браузер
  по SSE (`/sse/feed`, Фаза 6). Fallback — периодический `GET /api/listings?matched=true`.
- **Дедуп без Redis.** TTL-индексы MongoDB (`seen_listings`, `listings`).

## Процессы (контейнеры — Фаза 10)
`web` (Flask) · `poller` (asyncio) · `bot` (aiogram) · `mongo` (replica set, для Change Streams).
В dev — MongoDB Atlas (replica set из коробки).
