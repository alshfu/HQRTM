# Roadmap och Changelog

Fullständig plan — `HQRTM_ToR_Flask_MongoDB_Roadmap.md` (§11). Aktuell status — `CLAUDE.md`.

## Framsteg per fas
| Fas | Tema | Status |
|---|---|---|
| 0 | Förberedelse (repo, miljö, tooling, CI) | ✅ |
| 1 | MongoDB-datalager + multi-source-skelett | ✅ |
| 2 | Poller: FCFS-detektion + adaptrar + matchning (M1) | ✅ kod klar; adaptrar `enabled=False` (väntar nyckel/ToS) |
| 3 | Telegram-bot (M2) | 🟡 kärna klar (koppling + leverans, `bot/service.py`); kräver bot-token + alltid-på-process |
| 4 | Flask API + Auth | ✅ |
| 5 | Frontend (Jinja2 + Tailwind + Vanilla JS) + i18n + admin-UI | ✅ |
| 6 | Realtid (SSE + Change Streams) | ✅ |
| 7 | GitHub Pages demo | ✅ (demo publicerad) |
| 8 | Robusthet, säkerhet, observerbarhet | 🟡 påbörjad (loggar+PII, readiness, säkerhetsheaders, mätvärden) |
| 9 | Testning | ⏳ (unit/integration pågår, 121 passed) |
| 10 | Driftsättning (beta web-only, PaaS) | 🟡 scaffold klart (Dockerfile, render.yaml, poller-cron, --once, publik HomeQ-poll) — se [Deploy-Beta](Deploy-Beta) |
| 11 | Dokumentation och leverans | 🚧 (denna Wiki) |

## Changelog (kort)
- **2026-06-07** — Fas 0: skelett, miljö, pre-commit, CI.
- **2026-06-07** — Fas 1: modeller, index, multi-source-adaptrar.
- **2026-06-07** — Pivot: all-in-one-aggregator för svenska plattformar.
- **2026-06-07** — Fas 4: auth (JWT+Argon2), filter, listings, aviseringar, Telegram-link, OpenAPI.
- **2026-06-07** — Fas 6: realtid (SSE + Change Streams), dashboard med `EventSource`.
- **2026-06-07** — Fas 2: riktig HomeQ-adapter (Core API), Qasa-adapter (GraphQL, ej verifierad),
  filtermatchning → idempotent köning av aviseringar. Adaptrar `enabled=False`.
- **2026-06-07** — Fas 5: frontend (Tailwind + Vanilla JS), roller user/admin, **i18n (sv/en)**,
  **adminpanel** (`/api/admin/*`, `/app/admin`), **production-Tailwind-bygge**. → **v0.5.0**
- **2026-06-08** — Fas 2: **Samtrygg-adapter** (`GetHomePageObjects`, robust parsning: rum från
  adressen, fallback på fältnamn, gruppering per stad) + inställningar/tester. `enabled=False`
  (host/ToS ej bekräftade). Vitrinen på GitHub Pages gjordes om från «demo» till **release-presentation**.
- **2026-06-08** — Vitrinen översatt till **svenska** och visar **riktiga annonser från den verkliga
  parsern** (`scripts/gen_sample_listings.py` → `HQRTM-Demo/sample-listings.js`) med **länk till källan**
  i varje kort. Beslut: allt på svenska; riktiga data + källa; Telegram (Fas 3) uppskjuten.
- **2026-06-08** — Wiki översatt till **svenska** (alla sidor).
- **2026-06-08** — Annonser berikade med **bild** (`image_url`) och **beskrivning** (`description`):
  nya fält i `Listing`, normalisering i alla adaptrar (HomeQ/Qasa/Samtrygg), `pick_image`-hjälpare.
  Vitrinens urval visar nu bild + beskrivning + länk till källan.
- **2026-06-08** — **Fas 8 påbörjad**: `shared/logging.py` (strukturerade loggar + PII-maskering),
  `/health/ready` (DB-ping), säkerhetsheaders på alla svar, konfigurerbar rate-limit-backend
  (`RATELIMIT_STORAGE_URI`), pollerns mätvärden per cykel. 129 passed.
- **2026-06-08** — **Inga påhittade annonser**: fiktiva fixturer borttagna.
- **2026-06-08** — **Riktiga Göteborg-annonser i skyltfönstret**: HomeQ Card Search
  (`POST api.homeq.se/api/v3/cards/`) är publikt åtkomlig utan JWT → `HomeQAdapter.fetch_public_cards`
  hämtar och filtrerar på bbox (Göteborg), normaliserar med samma parser (bild + beskrivning + länk
  till förstakällan). Engångshämtning av publik data; adaptern kvar `enabled=False` (ingen 24/7-polling).
- **2026-06-08** — **Auto-uppdatering var 0,1 h** (`.github/workflows/refresh-vitrine.yml`): cron hämtar
  riktiga Göteborg-annonser och pushar → Pages bygger om. **Hela modulära demot** (flöde + adminpanel)
  drivs nu av riktig data (`window.HQRTM_SAMPLE`/`HQRTM_META`): riktiga bilder, källänk i modalen,
  admin visar region/antal/senaste hämtning. Device-snapshots är frysta referenser.
- **2026-06-08** — **Webbläsartillägg «Snabbansök»** (`extension/`, MV3): klient i användarens egen
  webbläsare — lokal profil/JWT, lista matchningar, öppna annonser, autofyll av presentation på
  annonssidor. Inga plattformslösenord, ingen autoinskickning (användaren skickar själv).
- **2026-06-08** — **Qasa aktiverad**: schemat avstämt mot live (`homeIndexSearch`, publik anonym
  sökning) → adaptern omskriven + `enabled=True`. Ger Qasa-marketplace (hela landet, ansökningsbaserad
  → FCFS), aggregerar även andra plattformar. 145 passed.
- **2026-06-08** — **Stockholm: Bostadsförmedlingen** tillagd via kommunalt öppet data-API
  (`bostad.stockholm.se`, ingen auth, `enabled=True`) — kö-baserad (`listing_type=queue`).
  **Engine lagrar nu alla annonser** (FCFS + kö); `only_fcfs`-filter styr vad användaren ser.
  Blocket (ToS) och Boplats (oklart) tillkommer ej utan legitim åtkomst. 147 passed.
- **2026-06-08** — **Ett-tryck-ansökan + ansökningsprofil**: «Ansök»-knapp i flödet och inline-knapp
  i Telegram (direkt till källans annons); `/api/profile` (GET/PUT) + sektion i Konto för att spara
  presentation/inkomst/kontakt och kopiera dem snabbt. (Ingen autoinloggning/autoansökan — endast
  legal genväg.) Tester: `test_profile.py`. 142 passed.
- **2026-06-08** — **Fas 3 (Telegram) implementerad** + **juridiska sidor**: `bot/service.py`
  (kontokoppling via engångskod + leverans av köade aviseringar, latency_ms/delivered),
  `bot/handlers.py` (aiogram `/start <kod>`), `bot/main.py` (long-polling + leveransloop).
  `/privacy` + `/terms` (svenska, GDPR) länkade från registreringen. Tester: `test_bot_service.py`,
  `test_legal.py`. 139 passed. Kräver `TELEGRAM_BOT_TOKEN` + alltid-på-process för boten.
- **2026-06-08** — **Beta-deploy-scaffold** (web-only, PaaS): `Dockerfile` (gunicorn/gthread) +
  `.dockerignore`, `render.yaml`, poller `--once` + publik HomeQ-poll (`HOMEQ_PUBLIC_POLL`/`HOMEQ_BBOX`),
  `ensure_indexes` vid pollerstart, `poll-homeq.yml` (cron → prod-Mongo), guide [Deploy-Beta](Deploy-Beta).

## Kända externa blockerare
- Poller: riktig bevakning av plattformarna väntar på aktivering av adaptrar (`enabled=True`) — kräver
  API-nyckel/åtkomst för HomeQ/Qasa och bekräftad ToS (ägarens beslut, se [Efterlevnad](Compliance)).
