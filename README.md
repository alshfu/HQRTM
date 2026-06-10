# HQRTM — HomeQ Real-Time Monitor

**All-in-one-aggregator** för bevakning av hyresbostäder på flera svenska plattformar
(HomeQ, Qasa, Samtrygg; vidare — Blocket Bostad, Bostad Direkt…). Bevakar publiceringar dygnet
runt, lyfter direkt fram **«Först till kvarn» (FCFS)**-annonser, sållar bort köbaserade, matchar mot
användarnas filter och levererar en avisering med länk i **Telegram på ≤ 1,5 s**. Webbpanel: filter,
Telegram-koppling, realtidsflöde (SSE), gränssnitt på **svenska och engelska**.

> Boten **loggar inte in** på plattformskonton och **ansöker inte** — den aviserar bara.

🔗 **Demo (UI, urval från den riktiga parsern):** https://alshfu.github.io/HQRTM/

## Stack

Flask 3 (API + Jinja2) · MongoDB (PyMongo + Motor) · separat asyncio-poller (`httpx`) ·
Telegram (`aiogram`) · realtid via MongoDB Change Streams + SSE · Vanilla JS ·
Tailwind CSS (production-bygge) · i18n sv/en.

Fullständig kravspec: [`HQRTM_ToR_Flask_MongoDB_Roadmap.md`](HQRTM_ToR_Flask_MongoDB_Roadmap.md) (kanon).
Utvecklingsguide (även för AI-assistenter): [`CLAUDE.md`](CLAUDE.md).
Detaljerad dokumentation — [**Wiki**](https://github.com/alshfu/HQRTM/wiki) (källor i [`docs/wiki/`](docs/wiki/)).

## Multi-source

Källan är isolerad i en adapter (`poller/sources/`, bas `SourceAdapter` + register). Alla plattformar
normaliseras till en kollektion `listings`; annonsens unikhet — paret **(source, external_id)**.
Lägga till en plattform = ny adapter, pollerkärnan ändras inte.

| Plattform | Adapter | Väg | Status |
|---|---|---|---|
| HomeQ | `poller/sources/homeq.py` | officiellt **Core API** (`/api/v2/tokens/` + Card Search) | implementerad, `enabled=False` (kräver nyckel + ToS) |
| Qasa  | `poller/sources/qasa.py`  | GraphQL `homes` | implementerad, kontrakt ej verifierat, `enabled=False` |
| Samtrygg | `poller/sources/samtrygg.py` | `GetHomePageObjects` (SwaggerHub) | implementerad, host/ToS ej bekräftade, `enabled=False` |

> ⚠️ En adapter aktiveras (`enabled=True`) först efter kontroll av plattformens ToS — se [`COMPLIANCE.md`](COMPLIANCE.md).

## Arkitektur (processer)

| Process | Syfte |
|---|---|
| `poller` | asyncio: bevakning av plattformar → FCFS-detektion → dedup → matchning mot filter → köning av aviseringar |
| `bot`    | Telegram-bot (aiogram): kontokoppling, leverans av aviseringar (Fas 3, uppskjuten) |
| `web`    | Flask: REST API, webbpanel, SSE-flöde, adminpanel |
| MongoDB  | lagring + Change Streams (replica set) |

Pollern är en **separat process**: högfrekvent bevakning dygnet runt är oförenlig med Flasks
request-response-modell. Kopplingen mellan processerna går via MongoDB (pollern skriver, web läser +
lyssnar på Change Stream).

## Lokal körning (dev)

Kräver **Python 3.12+** och åtkomst till MongoDB med replica set (rekommenderas **Atlas free-tier** —
replica set direkt).

```bash
# 1. Miljö
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 2. Hemligheter
cp .env.example .env        # fyll i MONGO_URI (Atlas) m.m.

# 3. Pre-commit-hooks (skyddar publikt repo mot läckta hemligheter)
pre-commit install

# 4. MongoDB-index (en gång per ny databas)
python -m shared.db

# 5. Starta webbappen (API + panel + adminpanel + SSE)
flask --app web.app run --debug      # http://127.0.0.1:5000/ , /health , /apidocs

# 6. Poller (separat process). Utan aktiverade adaptrar (enabled=True) säger loggen att inga finns.
# python -m poller.main

# 7. Telegram-bot (separat process) — Fas 3, uppskjuten
# python -m bot.main
```

CSS är redan byggd och incheckad (`web/static/css/app.css`) — Node behövs inte för att köra.
Bygga om stilar efter malländringar: `cd frontend-build && npm install && npm run build`
(se [`frontend-build/README.md`](frontend-build/README.md)).

## REST API

| Metod | Endpoint | Syfte |
|---|---|---|
| POST | `/auth/register`, `/auth/login`, `/auth/refresh` | Registrering/inloggning (JWT access+refresh) |
| GET/POST/PUT/DELETE | `/api/filters[/<id>]` | CRUD för filter |
| GET | `/api/listings` | Flöde (`?matched=true`, `source`, `listing_type`, `district`, paginering) |
| GET | `/api/notifications` | Aviseringshistorik (paginering) |
| POST/GET | `/api/telegram/link`, `/api/telegram/status` | Telegram-koppling |
| GET/DELETE | `/api/me` | Profil; radering av konto och data (GDPR) |
| GET/POST | `/api/admin/stats`, `/api/admin/users`, `/api/admin/users/<id>/role` | Adminpanel (roll `admin`) |
| GET | `/sse/feed` | Realtidsflöde av träffar (SSE, auth via `?token=`) |
| GET | `/health`, `/openapi.json`, `/apidocs` | Health-check, OpenAPI, Swagger UI |

Lösenord — Argon2; åtkomst till data — endast egen (JWT-kontroll). Fullständig referens —
[Wiki → API-Reference](docs/wiki/API-Reference.md).

## Internationalisering

Gränssnitt på **svenska (prioritet)** och **engelska**. Locale: `?lang=sv|en` → cookie → standard `sv`.
Kataloger — `web/i18n.py` (utan tredjepartsbibliotek); språkväxlare i UI.

## Konfiguration

Alla inställningar — via miljövariabler (se [`.env.example`](.env.example) och
[Wiki → Configuration](docs/wiki/Configuration.md)).
Bevakningsfrekvens: `POLL_INTERVAL_MS` (säker standard; tätare under «heta» timmar — `HOT_HOURS`).

## Utveckling

```bash
ruff check .        # lint
black .             # format
pytest              # tester (121 passed)
```

Förgrening: `main` (stabil) ← `develop` ← `feature/*`, ändringar via PR.
CI (`.github/workflows/ci.yml`): ruff + black + pytest vid push/PR mot `main`/`develop`.

## Status

Klart: **Fas 0, 1, 2 (kärna + adaptrar HomeQ/Qasa/Samtrygg), 4, 5, 6, 7**. Pågår/framåt: Telegram-leverans
(Fas 3, uppskjuten), robusthet/säkerhet (8), driftsättning på VPS (10). Riktig bevakning av plattformarna
väntar på aktivering av adaptrar (nycklar/ToS — ägarens beslut). Aktuell status — [`CLAUDE.md`](CLAUDE.md) och
[Wiki → Roadmap](docs/wiki/Roadmap-and-Changelog.md).

## Bidragsgivare

- **Alexander Shchetinin** — skapare och underhållare
- **Pushkinho (Petros)** — `Petros@maktic.se`

Vill du bidra? Se [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Licens

[MIT](LICENSE) · Efterlevnad (plattformarnas ToS + GDPR): [`COMPLIANCE.md`](COMPLIANCE.md).
