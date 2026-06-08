# Arkitektur

```
        Plattformar (HomeQ, Qasa, Blocket, Bostad Direkt, Samtrygg)
                         │ bevakning (1 gång för alla)
        ┌────────────────▼─────────────────────────────────────┐
        │  POLLER (asyncio, separat process)                    │
        │  sources/* (adaptrar) → detector(FCFS) → matcher → dispatcher │
        └───────┬───────────────────────────────────┬──────────┘
                │ listings / notifications           │ Telegram (aiogram)
        ┌───────▼────────────┐               ┌───────▼────────┐
        │      MongoDB        │◄─Change Stream│   Telegram Bot │
        │ users/filters/      │               └────────────────┘
        │ listings/notif/seen │
        └───────▲────────────┘
                │ PyMongo
        ┌───────┴───────────────────────────────┐
        │  FLASK (API + Jinja2 + SSE)            │── SSE ─► Webbläsare (Tailwind+JS)
        └────────────────────────────────────────┘
```

## Principer
- **Pollern är en separat process.** Flask är synkron (WSGI); högfrekvent bevakning dygnet runt är
  oförenlig med request-response. Kopplingen web↔poller går via MongoDB.
- **Multi-source.** Varje plattform är en adapter `SourceAdapter` i `poller/sources/`, registrerad i
  registret. Allt normaliseras till kollektionen `listings` med fältet `source`. Lägga till en plattform =
  ny adapter, pollerkärnan ändras inte. Aktivering av en adapter (`enabled=True`) — först efter ToS-kontroll.
- **Realtid.** Pollern skriver en träff → Flask lyssnar på Change Stream `notifications` → skickar till
  webbläsaren via SSE (`/sse/feed`, Fas 6). Fallback — periodiskt `GET /api/listings?matched=true`.
- **Dedup utan Redis.** MongoDB TTL-index (`seen_listings`, `listings`).

## Processer (containrar — Fas 10)
`web` (Flask) · `poller` (asyncio) · `bot` (aiogram) · `mongo` (replica set, för Change Streams).
I dev — MongoDB Atlas (replica set direkt).
