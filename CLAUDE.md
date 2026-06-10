# CLAUDE.md — handledning för AI-assistenten i projektet HQRTM

> Den här filen är ingångspunkten för varje AI-assistent (Claude Code m.fl.) som arbetar med projektet.
> Läs den **först**, före varje åtgärd. Håll den uppdaterad: efter
> betydande beslut och ändringar — uppdatera avsnitten ”Nuvarande tillstånd” och ”Beslutslogg” längst ner.

---

## 1. Vad är det här för projekt

**HQRTM** — en **all-in-one-aggregator** för bevakning av bostadsuthyrning på flera svenska plattformar
(HomeQ — den första; därefter Qasa, Blocket Bostad, Bostad Direkt, Samtrygg, Bostadsförmedlingen, Boplats…).
Bevakar publiceringar dygnet runt, lyfter omedelbart fram annonser av typen **”Först till kvarn” (FCFS)**,
sållar bort ”kö”-annonser (queue), matchar mot användarnas filter och levererar en avisering
med länk till **Telegram inom ≤ 1.5 s**. Webbpanel: filter, koppling av Telegram, live-flöde.

> **Multi-source (beslut 2026-06-07):** källan är isolerad i en adapter `poller/sources/`
> (bas `SourceAdapter` + register). Alla plattformar normaliseras till en enda kollektion `listings`
> med fältet `source`; en annons är unik via paret **(source, external_id)**. Att lägga till en plattform =
> en ny adapter, pollerns kärna ändras inte. ⚠️ ToS/robots.txt — **separat för varje plattform**
> (checklista i `COMPLIANCE.md`); adaptern blir `enabled=True` först efter ett positivt utlåtande.

**Utanför scope (viktigt):** boten loggar **inte** in på plattformskonton och skickar **inte** in ansökningar — den aviserar bara.

---

## 2. ⚠️ DET VIKTIGASTE: vilken stack som ska anses kanonisk

I repot finns tre kravspecifikationer, och de **motsäger varandra teknologimässigt**. Det är inget lässfel —
det är idéns utveckling. Kanonisk är det **senaste och mest detaljerade** dokumentet:

### ✅ Källa/kanon: `HQRTM_ToR_Flask_MongoDB_Roadmap.md`

Godkänd stack:

| Lager | Teknologi |
|---|---|
| Backend API + Web | **Flask 3.x** (Python 3.12+) + **Jinja2**-mallar |
| Poller / worker | **Separat** asyncio-process: `httpx` + `asyncio` (+ `Playwright` fallback) |
| Telegram | `aiogram` (async) |
| Databas | **MongoDB** (PyMongo för Flask, Motor för async-workern) |
| Real-time | **MongoDB Change Streams + SSE** (`EventSource`), INTE WebSocket |
| Frontend-stilar | **Tailwind CSS** eller **Bootstrap 5** (valet ännu inte fastställt — se §6) |
| Frontend-logik | **Vanilla JavaScript** (`fetch`, `EventSource`), INTE React |
| Repository | **GitHub public** |
| Demo | **GitHub Pages** (statik + mockdata) |
| Driftsättning | Docker + docker-compose på VPS, Nginx + TLS |

### ⚠️ Föråldrade/alternativa kravspecar — implementera INTE som de är

- **`HQRTM_ToR_Backend.md`** — tidigt proposal: FastAPI + PostgreSQL + Redis + WebSocket.
  Använd den **bara** som källa till detaljerade krav (ID av typen `BE-DE-001`, budget för
  latens, NFR, risker). De konkreta teknologierna (FastAPI/Postgres/Redis) är **ersatta** med
  Flask/MongoDB/Change Streams i Roadmap. SQL-schemat i den är konceptuellt; den verkliga
  datamodellen finns i Roadmap §3 (MongoDB-kollektioner).
- **`HQRTM_ToR_Frontend.md`** — tidigt proposal för frontend: React + TypeScript + Vite + WebSocket.
  Använd den också som källa till UX-krav (ID `FE-AU-001` osv.), men teknologin är
  Jinja2 + Vanilla JS enligt Roadmap, inte React/SPA.

**Om ett krav motsäger sig mellan dokumenten vinner Roadmap.** Om du är osäker
på vilken stack en uppgift hör till — fråga användaren, välj inte tyst.

> Terminologi: i Backend ToR kallas real-time `WS /ws/feed` (WebSocket). I den kanoniska
> stacken är det **SSE `/sse/feed`**. Förväxla inte.

---

## 3. Projektets nuvarande tillstånd (per 2026-06-07)

**Det finns ännu ingen applikationskod**, men git och publiceringen av demot är redan uppsatta. I repot:

```
HQRTM/
├── HQRTM_ToR_Flask_MongoDB_Roadmap.md   # ✅ kanon: stack + fullständig roadmap (faser 0–11)
├── HQRTM_ToR_Backend.md                 # ⚠️ tidigt proposal (krav — ja, stack — nej)
├── HQRTM_ToR_Frontend.md                # ⚠️ tidigt proposal (krav — ja, stack — nej)
├── CLAUDE.md                            # den här filen
├── index.html                           # GitHub Pages-skyltfönster: CTA till appen + device-snapshots + demo-inloggningar
├── HQRTM-Demo/
│   ├── index.html                       # ✅ huvuddemot: modulär React-app (Babel i webbläsaren)
│   ├── app/*.jsx  styles/*.css  tweaks-panel.jsx   # moduler i den modulära versionen (laddas via HTTP)
│   └── HQRTM-{Desktop,Tablet,Mobile}.html          # self-contained device-snapshots (frame-locked)
├── pyproject.toml                       # beroenden + ruff/black/pytest (källa/kanon)
├── .env.example  README.md  COMPLIANCE.md  CONTRIBUTING.md  LICENSE(MIT)
├── .pre-commit-config.yaml  .secrets.baseline   # ruff/black/detect-secrets
├── .github/workflows/ci.yml             # CI: ruff + black + pytest (push/PR till main|develop)
├── shared/   # config.py (pydantic-settings), db.py, models.py, utils.py
├── web/      # app.py (Flask factory + /health), auth/ api/ sse/ templates/ static/
├── poller/   # main.py, homeq_adapter.py, detector.py, matcher.py, dispatcher.py (platshållare)
├── bot/      # main.py, handlers.py (platshållare)
├── tests/    # test_smoke.py, test_utils.py
├── .gitignore                           # skydd för public repo (.env, .venv, .idea, ...)
├── .venv/  (ignored)                    # Python 3.12
└── .idea/  (ignored)
```

**Klart:**
- ✅ Git: repo **https://github.com/alshfu/HQRTM** (public). Grenar `main` (stabil) och `develop`.
- ✅ GitHub Pages: **https://alshfu.github.io/HQRTM/** (source `main`/roten) — demot levereras (200).
- ✅ **Fas 0 avslutad** (kod): paketstruktur, `pyproject.toml`, venv 3.12, `.env.example`,
  README/COMPLIANCE/CONTRIBUTING/LICENSE(MIT), pre-commit (ruff/black/detect-secrets), CI `ci.yml`.
  Lint/format/tester gröna (`ruff`, `black --check`, `pytest` — 10 passed). `web/app.py` levererar `/health`.
- ⚠️ Mall-`main.py` (PyCharm) borttagen.

**Ännu INTE gjort:** GitHub Wiki (skelett), GitHub Project/Issues — valfritt; `COMPLIANCE.md`
är ifylld bara som skelett (ToS HomeQ + GDPR — TODO innan Fas 2). Härnäst — **Fas 1** (datalager MongoDB).

> ⚠️ Demot i `HQRTM-Demo/` är **designprototyper** (React + Babel-in-browser, mockdata), inte den slutgiltiga frontenden.
> Den skarpa frontenden enligt kanon är Jinja2 + Tailwind/Bootstrap inuti `web/` (Fas 5). Prototyperna är UI-referens.
>
> Demo-inloggningar (förifyllda automatiskt på inloggningsskärmen): **user** `elin@hqrtm.se` / `demo1234`,
> **admin** `admin@hqrtm.se` / `admin1234`. Kontona definieras i `HQRTM-Demo/app/data.jsx` (`DEMO_CREDS`).
> Den modulära versionen (`HQRTM-Demo/index.html`) laddar `app/*.jsx` via Babel → **fungerar bara via HTTP**
> (GitHub Pages / lokal server), inte via `file://`. Device-snapshots är självständiga och öppnas som fil.

**Vi befinner oss i början av Fas 1** (datalager MongoDB). Fas 0 är avslutad.

---

## 4. Målstruktur för repot (skapas allteftersom arbetet fortskrider)

Från Roadmap §2. Varje process är en separat container i docker-compose.

```
hqrtm/
├── README.md  COMPLIANCE.md  LICENSE  CONTRIBUTING.md
├── .gitignore  .env.example  docker-compose.yml
├── pyproject.toml / requirements.txt
│
├── poller/        # async-worker: main.py, homeq_adapter.py, detector.py, matcher.py, dispatcher.py, config.py
├── bot/           # Telegram (aiogram): main.py, handlers.py
├── web/           # Flask: app.py, config.py, auth/, api/, sse/, templates/, static/
├── shared/        # db.py (MongoDB + index), models.py (pydantic-scheman)
├── frontend-build/# Tailwind/Bootstrap-bygge
├── demo/          # statik för GitHub Pages (index.html, assets/, mock-data.js)
├── tests/         # unit / integration / e2e
└── .github/workflows/  # ci.yml, deploy-pages.yml, deploy-vps.yml
```

**Arkitekturprincip nr 1:** Flask är synkront (WSGI), därför **får** den högfrekventa pollingen 24/7
**inte** ligga i Flask-handlers. Pollern är en **separat, långlivad asyncio-process**.
Flask ansvarar bara för API och webb. Kopplingen dem emellan sker **via MongoDB** (pollern skriver,
Flask läser + lyssnar på Change Stream).

---

## 5. Datamodell (MongoDB, från Roadmap §3)

Kollektioner: `users`, `filters`, `listings`, `notifications`, `seen_listings`, `audit_log`.

Implementerat i Fas 1: `shared/models.py` (pydantic-scheman för alla kollektioner, StrEnum för source/type/
status), `shared/db.py` (`ensure_indexes()` + kollektionsnamn `COLL_*` + CLI `python -m shared.db`).

Kritiska invarianter (ska alltid efterlevas):
- **En annons är unik via det sammansatta `(source, external_id)`** (multi-source; förtydligar DB-001).
  Index `uniq_source_extid`. Samma `external_id` på olika plattformar är olika annonser.
- **TTL-index `seen_listings.seen_at`** (~24 h, `seen_ttl_hours`) → dedup utan Redis (DB-002).
- **TTL-index `listings.fetched_at`** (~7 dagar) → autorensning (DB-003).
- **Lösenord — bara hash** (Argon2/bcrypt), hemligheter — aldrig i klartext (DB-004).
- **`notifications.latency_ms`** (publish → delivered) skrivs för SLA-rapportering (DB-005).
- **MongoDB i replica set-läge** (minst single-node RS) — obligatoriskt för Change Streams (DB-006).

---

## 6. Beslut (delvis stängda 2026-06-07)

**✅ Antaget:**
- **Python 3.12** (venv återskapad). **MongoDB — Atlas free-tier** (MONGO_URI i `.env`). **Licens — MIT**.

**❓ Fortfarande öppet — fråga, välj inte tyst:**
1. **HomeQ:** ✅ officiellt API bekräftat (Core API, kontraktet avstämt 2026-06-07 — se
   `COMPLIANCE.md` och `poller/sources/homeq.py`). **Kvarstår som blockerare:** skaffa konto/integrations-
   nyckel från landlord-portalen + slutgiltigt bekräfta ToS för läsåtkomst för en consumer-tjänst
   (ägarens åtgärd). Adaptern är skriven och testad, men `enabled=False` tills dess.
2. ✅ **Frontend CSS: Tailwind** (beslutat 2026-06-07). Just nu — Play CDN (prototyp); production-bygget
   i `frontend-build/` (Tailwind CLI, se README där) — flytten sker i polering/Fas 8.
3. ✅ **UI-språk — svenska (prioriterat)**, produkt för den svenska marknaden (beslutat 2026-06-07).
   Engelska — sekundärt (i18n-arkitektur förberedd för tillägg). HELA gränssnittstexten skrivs
   på svenska (Logga in, Flöde, Filter, Aviseringar, Konto …); strängar — förbereds för i18n.
4. Monetisering/prisplaner och adminpanel nu? (som standard — nej; i demot finns admin som UI).
5. Förväntat antal användare (påverkar valet av VPS) — till Fas 10.

---

## 7. Roadmap — var vi är och vad som kommer härnäst

Fullständig plan i Roadmap §11. Kort karta över faser och milstolpar:

- **Fas 0** — ✅ KLAR: repository, struktur, miljö, pre-commit, CI.
- **Fas 1** — ✅ KLAR (kod, på grenen `feature/phase1-data-layer`): `shared/models.py`,
  `shared/db.py` (`ensure_indexes`), multi-source-stomme `poller/sources/`. Tester 22 passed.
  Kvarstår: köra `python -m shared.db` mot riktiga Atlas (kräver MONGO_URI från ägaren).
- **Fas 2** — 🟡 KÄRNAN KLAR (M1): `poller/detector.py` (FCFS vs kö), `poller/dedup.py`
  (seen_listings), `poller/engine.py` (dedup→detektion→sållning→upsert), `poller/main.py` (async-loop,
  adaptiv frekvens HOT_HOURS, backoff). Tester 58 passed. **Verkliga adaptrar avstängda**
  (`enabled=False`) — väntar på API-åtkomst/ToS. ToS-research nedtecknad i `COMPLIANCE.md`:
  **HomeQ/Qasa har ett officiellt Core API** (`docs-core.homeq.se`, JWT + Card Search + webhooks) —
  prioriterad väg; Blocket/Bostad Direkt/Samtrygg — kräver partneråtkomst/kontroll. **Ägarens
  åtgärd:** begära API-nyckel för HomeQ/Qasa.
  **Verklig HomeQ-adapter implementerad** (`poller/sources/homeq.py`: auth `/api/v2/tokens/` JWT +
  Card Search `/api/v3/cards/` FCFS-only + normalisering + backoff på 429/5xx). **Matchning klar**
  (`poller/matcher.py` + `engine.enqueue_notifications` → queued-aviseringar, idempotent;
  blåser liv i webbflödet/SSE utan Telegram). Gren `feature/phase2-homeq-adapter`, **80 passed**.
  Kvarstår: aktivera adaptern `enabled=True` (konto + ToS) och leverans till Telegram (Fas 3).
- **Fas 3** — Telegram → **milstolpe M2** (testaviseringar med länk kommer fram).
- **Fas 4** — ✅ KLAR: auth (register/login/refresh, Argon2, JWT), rate-limit, CRUD `/api/filters`,
  `/api/me` (GDPR), `/api/listings` (matched + paginering), `/api/notifications` (paginering),
  `/api/telegram/link|status`, OpenAPI (`/openapi.json`) + Swagger UI (`/apidocs`). Tester 39 passed.
- **Fas 5** — ✅ KLAR: Jinja2 + **Tailwind (production-bygge)** + Vanilla JS. Sidorna
  landing/login/register, panel (dashboard-flöde, filter CRUD, aviseringar, inställningar+GDPR),
  JS-klient `web/static/js/api.js` (tokens, auto-refresh, guard), roll user/admin i navigeringen.
  Rutter — `web/views.py`. **i18n (sv/en)** (`web/i18n.py`), **admin-UI** (`web/admin/`, `admin.html`),
  **production Tailwind** (`frontend-build/` → `web/static/css/app.css`, purged+minified, incheckat;
  Play CDN borttaget ur `base.html`).
- **Fas 6** — ✅ KLAR: SSE + Change Streams. `web/sse/` (broker pub/sub + watcher Change Stream
  `notifications` + endpoint `/sse/feed`, auth via `?token=`). Dashboard: `EventSource` med dedup,
  auto-reconnect, live-indikator, fallback till polling. Tester 51 passed. (Watcher kräver replica set;
  vid flera web-processer behövs en gemensam backend — Fas 8/10.)
- **Fas 7** — GitHub Pages demo.
- **Fas 8** — robusthet/säkerhet/observerbarhet.
- **Fas 9** — testning.
- **Fas 10** — driftsättning på VPS → **milstolpe M3** (48-timmarskörning).
- **Fas 11** — dokumentation och överlämning.

**Latensbudget (mål ≤ 1.5 s):** polling ~0.5–0.8 s · request+parsning ~0.2–0.3 s ·
detektion+matchning ~0.05–0.15 s · sändning till Telegram ~0.2–0.4 s. Väg varje beslut mot den.

---

## 8. Arbetsregler (ska efterlevas strikt)

### Säkerhet / hemligheter (repot är publikt!)
- **Inte en enda hemlighet i kod eller git-historik.** Telegram-token, Mongo URI, JWT-secret —
  bara via `.env` (i `.gitignore`) och GitHub Secrets.
- Innan första commit: konfigurera **pre-commit med detect-secrets** (skydd för public repo).
- Loggar — **utan PII** (e-mail, telegram_chat_id m.m. ska inte loggas).
- Lösenord — Argon2/bcrypt. TLS i prod.

### Compliance (innan scraping/polling påbörjas)
- Kontrollera ToS för HomeQ och `robots.txt`, slutsatser → `COMPLIANCE.md`. Officiellt API har prioritet.
- Etisk belastning: en central poller för alla, rimliga intervall, jitter,
  exponentiell backoff, respekt för `429/503/Retry-After`, rotation av User-Agent.
- GDPR: samtycke vid registrering, integritetspolicy, rätt till radering av data (`DELETE /api/me`).

### Kod och kvalitet
- **Python 3.12** (venv: `/usr/local/bin/python3.12`). Installation: `pip install -e ".[dev]"`.
  Scraping-beroenden — separat extra: `pip install -e ".[scraper]" && playwright install`.
- Lint/format: **ruff + black** (config i `pyproject.toml`, rad ≤ 100). Tester: **pytest**
  (`pytest -q`). Före commit kontrollerar pre-commit allt; i CI — `ci.yml`.
- Tester: unit på `detector`/`matcher`, integration med `mongomock` eller test-container, e2e med Playwright.
- HomeQ-parsern är isolerad i `HomeQAdapter` — vid ändring av källan rättas **bara den** (BE-DE-005).
- Pollingintervallet är konfigurerbart (`POLL_INTERVAL_MS`), säkert default, beskrivs i README.
- Idempotens: en omstart får inte ge dubbletter av aviseringar.

### Git / process
- Förgrening: `main` ← `develop` ← `feature/*`, via PR.
- **HUVUDREGEL (2026-06-08): vid varje avslutat steg — committa, pusha och uppdatera Wiki**
  (`docs/wiki/` + vid behov `scripts/sync-wiki.sh`), utan separat förfrågan. Pages-skyltfönstret
  levereras från `main` → ändringar i `index.html` pushas till `main`. (Upphäver det tidigare ”pusha bara på begäran”.)
- Spårbarhet: vid implementering av ett krav, hänvisa till dess ID (`BE-DE-001`, `FE-FL-003` o.s.v.).

### Interaktion med användaren
- Kommunikationsspråk — **ryska** (användaren skriver på ryska).
- Vid motsägelse i kravspecarna — Roadmap är överordnad; vid tvetydighet enligt §6 — **fråga**, gissa inte.

---

## 9. Notis om underhåll av den här filen

Efter varje betydande session, uppdatera de två blocken nedan. Det låter nästa AI fortsätta
utan att återupptäcka kontexten.

### Nuvarande tillstånd (uppdatera)

> **▶ FORTSÄTT HÄR (handoff 2026-06-08).** Betan är **LIVE**: web https://hqrtm.onrender.com
> (Render free, sover efter ~15 min), testkonto `petros`/`petrosBest`. **Atlas** kluster
> `cluster0.hm5obgl` (projekt «Mer info hunter», `60b56cac2612f0624616d4dd`), db-user `hqrtm`,
> nät 0.0.0.0/0. `MONGO_URI` i lokal `.env` (gitignored); GitHub-secret `PROD_MONGO_URI` satt;
> Render env `MONGO_URI` satt manuellt. CLI: `atlas` inloggad, `render` EJ inloggad. **Cron
> `poll-homeq.yml`** (var 6 min) bevakar 3 källor → prod: HomeQ (Göteborg), Bostadsförmedlingen
> (Stockholm), Qasa (**Göteborg + Stockholm** via `QASA_AREAS`). `render.yaml` = endast free web
> (bot-worker bortkommenterad); `buildFilter` tillagd men EJ re-synkad i Render. Webbtillägg i
> `extension/` (byggt, ej publicerat).
> **Nästa:** (1) re-synka Blueprint för buildFilter (inkl. nya env COOKIE_SECURE/RATELIMIT_STORAGE_URI);
> (2) Telegram-bot (token + alltid-på/betald worker); (3) riktig juridisk enhet i Privacy/Terms;
> (4) publicera tillägget (Chrome Web Store/AMO); (5) ev. Redis-instans för delad rate-limit vid
> uppskalning. **Gräns:** ingen autoclicker/lösenordslagring (Beslutslogg).

- **2026-06-10 (Fas 8 — httpOnly JWT-cookies + Redis rate-limit):** **Säkerhet.** `web/auth/cookies.py`
  (`set_/clear_auth_cookies`): login/register/refresh sätter `hqrtm_access`/`hqrtm_refresh` som
  **httpOnly**-cookies (`SameSite=Lax`; `Secure` via `COOKIE_SECURE` i prod) — additivt, JSON-tokens
  finns kvar för **Bearer** (API/tillägget). `require_auth` (web/deps.py) + SSE (`web/sse/routes.py`) +
  `/auth/refresh` läser cookie som fallback; nytt **`/auth/logout`** rensar dem. Webbpanelen
  (`web/static/js/api.js`) lagrar **inte längre token i localStorage** (XSS-skydd) → `credentials:
  same-origin` + en icke-känslig UX-flagga `hqrtm_session`; `EventSource("/sse/feed")` utan `?token=`.
  `settings/privacy/dashboard`-mallar uppdaterade. **Rate-limit:** `redis>=5` i beroendena så
  `RATELIMIT_STORAGE_URI=redis://…` ger delade räknare över processer; `render.yaml` sätter
  `COOKIE_SECURE=true` + `RATELIMIT_STORAGE_URI` (sync:false). Config `cookie_auth/cookie_secure/
  cookie_samesite`. Tester `test_auth_cookies.py` (5). **153 passed**, ruff/black gröna.
- **2026-06-10 (tillägg: ikoner + fältmappning, v0.2.0):** `extension/icons/` (16/32/48/128 px)
  genererade **utan beroenden** (`gen_icons.py`: grön rundad kvadrat + vitt hus, supersampling) och
  inkopplade i manifest (`icons` + `action.default_icon`). `content.js` fick **fältmappning**:
  knappen «Fyll i formuläret» matchar profilfälten (presentation/sysselsättning/inkomst/telefon/
  hushåll/inflytt) heuristiskt mot sidans `input`/`textarea`/`select` — etikett (`label`/`aria`/
  omslutande text) väger tyngst, sedan `name`/`id`/`placeholder`/`autocomplete`, plus typbonus;
  `PLATFORM_HINTS` ger direkta selektorträffar per domän. Värden sätts via **native value-setter** +
  `input`/`change` (React/Vue reagerar), datum→`yyyy-mm-dd`, belopp→siffror. «Endast presentation»
  kvar som fallback. **Ingen autoinskickning** (Beslutslogg). JS/JSON validerade (`node --check`).
- **2026-06-10 (Qasa per ort):** GraphQL-argumentet `homeIndexSearch(params: {areaIdentifier:
  "se/<stad>"})` avstämt mot live-API (probning via felmeddelanden, som tidigare). Ny konfig
  `qasa_areas`/`QASA_AREAS` (kommaseparerat, tomt = hela landet); adaptern hämtar varje ort separat
  via `documents(limit:)` och slår ihop med dedup på id. Cron `poll-homeq.yml` sätter
  `QASA_AREAS=se/goteborg,se/stockholm` → Qasa bevakar nu samma metroområden som övriga källor
  (live-smoke: 100 annonser, enbart Göteborg/Stockholm m. förorter). Tester `test_qasa_adapter.py`
  (per-ort + dedup + landsomfattande). **148 passed**, ruff/black gröna.
- **2026-06-08 (webbläsartillägg «Snabbansök»):** Legitim klient i `extension/` (Manifest V3): körs i
  användarens egen webbläsare, sparar JWT + ansökningsprofil **lokalt** (`chrome.storage.local`), listar
  matchningar (`/api/listings?matched`), öppnar annonser, badge med antal, och en hjälppanel på
  annonssidor (homeq.se/qasa.com/bostad.stockholm.se) som kopierar profil + fyller presentationen i
  formuläret. **Inga plattformslösenord lagras; ingen automatisk inskickning** — användaren granskar och
  skickar själv (linje från Beslutslogg: autoclicker byggs inte). `popup/content/background.js` + README.
  JS/JSON validerade, allt på svenska.
- **2026-06-08 (Qasa aktiverad):** Qasas publika anonyma marketplace-sökning avstämd mot live
  (`api.qasa.com/graphql` → `homeIndexSearch { documents { nodes {...} } }`, introspektion av,
  fält upptäckta via felmeddelanden). `poller/sources/qasa.py` omskriven (riktiga fält: rent/roomCount/
  squareMeters/location/uploads/platform), URL `qasa.com/p/<id>`, bild ur `uploads`, FCFS (ingen köpoäng).
  `enabled=True`. Live: 20 annonser (hela landet). Tester **145 passed**. Aktiva källor i cron:
  HomeQ (Göteborg) + Bostadsförmedlingen (Stockholm) + Qasa (hela landet).
- **2026-06-08 (Stockholm-källa + engine lagrar alla annonser):** **Bostadsförmedlingen i Stockholm**
  tillagd (`poller/sources/bostadsformedlingen.py`) via kommunalt **öppet data-API**
  (`bostad.stockholm.se/AllaAnnonser/?vy=lista`, ingen auth) — `enabled=True`. Kö-baserad → annonser
  taggas `listing_type=queue`. **Engine ändrad:** `process_new_listings` LAGRAR nu alla annonser
  (FCFS + kö), inte bara FCFS — kö-plattformar blir bevakningsbara; vad användaren ser/aviseras styrs
  av filtrens `only_fcfs`. Live-hämtning: 397 Stockholm-annonser. Tester **147 passed**.
  ⚠️ **Blocket** (Schibsten ToS mot skrapning) och **Boplats** (oklart API/ToS) tillkommer EJ utan
  legitim åtkomst. Cron-pollern (enabled-adaptrar) bevakar nu Göteborg (HomeQ) + Stockholm (Bostadsförm.).
- **2026-06-08 (ett-tryck-ansökan + ansökningsprofil):** «Ansök»-knapp i flödet (`dashboard.html`,
  `btn-accent`) och inline-knapp «🏠 Ansök nu» i Telegram-aviseringen → direkt till källans annons
  (legal genväg, ingen autoinloggning/autoansökan — autoclicker avböjd, se Beslutslogg). **Ansöknings-
  profil**: `User.applicant_profile`, `GET/PUT /api/profile`, sektion i Konto (presentation/occupation/
  income/phone/household/move_in + «Kopiera»). i18n sv/en, app.css ombyggd. Tester **142 passed**.
- **2026-06-08 (Fas 10 — beta-deploy-scaffold, web-only/PaaS):** Beslut: beta **web-only** (ingen
  Telegram), **PaaS (Render)**, data via **publik HomeQ**. Levererat: `Dockerfile` (gunicorn gthread,
  delad image för web+poller), `.dockerignore`, `render.yaml` (web), poller `--once`-läge + **publik
  HomeQ-bevakning** (`HOMEQ_PUBLIC_POLL`/`HOMEQ_BBOX`/`HOMEQ_PUBLIC_LIMIT`; `HomeQAdapter(public=True)`
  → `fetch_public_cards`), `ensure_indexes` vid pollerstart, `.github/workflows/poll-homeq.yml`
  (cron var 6:e min → prod-Mongo). Guide: `docs/wiki/Deploy-Beta.md`. pyproject: `gunicorn` + packages
  via `find`. Tester **131 passed**, ruff/black gröna. **Återstår (ägaråtgärd):** Atlas M0 + Render-konto
  + secrets (`MONGO_URI`, repo `PROD_MONGO_URI`), integritetspolicy/villkor (GDPR, idag platshållare).
- **2026-06-08 (auto-uppdatering + riktig data i hela demot):** GitHub Actions
  `.github/workflows/refresh-vitrine.yml` kör `gen_sample_listings.py` **var 6:e minut** (0,1 h) →
  hämtar riktiga Göteborg-annonser (HomeQ publik Card Search) → pushar `sample-listings.js` → Pages
  bygger om. Generatorn skriver även `window.HQRTM_META` (antal/region/tid). **Hela det modulära demot
  (`HQRTM-Demo/index.html`) drivs nu av riktig data:** index.html laddar `sample-listings.js`; `data.jsx`
  mappar `HQRTM_SAMPLE` → flödet (riktiga bilder via resize-proxy + länk till källan i modalen);
  **adminpanelen** (`screens-admin.jsx`) visar riktig region/antal objekt/senaste hämtning + en riktig
  händelse i loggen. `ListingCard`/`Photo` renderar riktig bild. ⚠️ Device-snapshots (Desktop/Tablet/
  Mobile.html) är **frysta** designreferenser — de uppdateras inte. 131 passed, ruff/black gröna.
- **2026-06-08 (bild/beskrivning + Fas 8 påbörjad):** Annonser berikade med `image_url` och
  `description` (modell + alla adaptrar + `pick_image`); skyltfönstrets urval visar bild, beskrivning
  och länk till förstakällan. **Fas 8 påbörjad:** `shared/logging.py` (strukturerade loggar +
  PII-maskering, JSON via `LOG_JSON`), `/health/ready` (DB-ping), säkerhetsheaders på alla svar,
  konfigurerbar rate-limit-backend (`RATELIMIT_STORAGE_URI`), pollerns mätvärden per cykel. Allt på
  svenska. Tester **129 passed**, ruff/black gröna. Hela repot är fritt från kyrilliska (svenska överallt).
- **2026-06-08 (skyltfönster på svenska + verklig parserdata + länkar till förstakällan):**
  Skyltfönstret `index.html` är helt översatt till **svenska** och visar **ett urval verkliga annonser
  från en riktig parser**: `scripts/gen_sample_listings.py` kör adaptrarna HomeQ/Qasa/Samtrygg
  genom `httpx.MockTransport` på fixturer (utan live-scraping — ToS efterlevs) → normaliserade
  `Listing` → `HQRTM-Demo/sample-listings.js` (`window.HQRTM_SAMPLE`). Varje kort är klickbart
  och leder till **förstakällan** (`url`: homeq.se/qasa.com/samtrygg.se). Tester **121 passed**,
  ruff/black gröna. ⚠️ Fas 8 (observerbarhet) — pausad (utkastet återställt), görs som ett separat
  steg. **OBS:** enligt ägarens beslut pågår översättning av **hela** kodbasen och dokumenten till svenska
  (CLAUDE.md, Wiki, kommentarer) — stegvis (se Beslutslogg).
- **2026-06-08 (Fas 2 — Samtrygg-adapter + skyltfönster→release):** Adaptern `poller/sources/samtrygg.py`
  förts till fungerande skick enligt mönster av qasa: inställningarna `samtrygg_api_url/public_base/timeout_s`
  i `shared/config.py` + `.env.example`, inkopplad i `poller/sources/__init__.py` (`@register`
  fungerar — verifierat), guard vid tomt `SAMTRYGG_API_URL`. **Parsning förstärkt:** utvinning av
  antal rum ur adress/rubrik (`N rok/rum`, fältet saknas i svaret), fallback via alt. fältnamn
  (`sqareMeters`→`squareMeters`/`area`, `price`→`rent`), robust genomgång av svaret `GetHomePageObjects`
  (gruppering per städer `RentalObjectInfo` / platt lista / wrapper `results`). Tester
  `tests/test_samtrygg_adapter.py` (11). Hela sviten **121 passed**, ruff/black gröna.
  ⚠️ `enabled=False` — host i SwaggerHub-specen är inte angiven, ToS inte bekräftat (aktivering hos ägaren).
  **GitHub Pages-skyltfönstret (`index.html`) gjort om från ”demo” till ”release”:** demo-disclaimern borttagen,
  block med verkliga funktioner tillagt (Faserna 0–6: multi-source, FCFS, matchning, SSE, API/JWT, panel+i18n,
  compliance — med markeringar live/Fas 3 för Telegram), länkar till GitHub/Wiki/Releases. Den interaktiva
  prototypen behållen som ”UI-preview av release” (ärligt: den skarpa backenden fungerar inte på statik). ⚠️ Filen
  är ännu inte incheckad/pushad till Pages — publicering hos ägaren.
- **2026-06-07 (Fas 5 — production Tailwind build, FAS 5 STÄNGD):** Flytt från Play CDN till
  byggd Tailwind. Tema (accent/typsnitt) och custom-komponenter (`.card/.input/.btn-accent/
  .navlink`) flyttade ut ur inline `base.html` till `frontend-build/` (`input.css` + `tailwind.config.js`,
  `content` skannar mallar och `api.js` → klasser ur inline-JS skärs inte bort). Bygget
  `npm run build` → `web/static/css/app.css` (purged+minified, 11KB, **incheckat** — deploy/CI
  behöver inte Node). `base.html` laddar `app.css` istället för CDN-skriptet. README för bygget uppdaterad.
  Tester **110 passed**, ruff/black gröna. Milstolpe: **Fas 5 helt avslutad.**
- **2026-06-07 (Fas 5 — i18n + admin-UI):** **i18n (sv/en)** utan flask-babel: `web/i18n.py`
  (kataloger sv/en, `translate()` med fallback sv→nyckel, `init_i18n()` — resolv av locale `?lang=`→cookie
  `hqrtm_lang`→default sv, Jinja-globaler `t/locale/locales`, vidareföring av katalogen till JS `window.HQRTM_I18N`).
  `HQRTM.t()` i `api.js` översätter inline-JS-strängar. Alla mallar översatta till `t()`, tillagd
  språkväljare `_lang.html` (SV|EN). **Admin-UI:** `require_admin` (roll från DB) i `web/deps.py`,
  blueprint `web/admin/routes.py` (`/api/admin/stats|users`, rollbyte med skydd mot själv-degradering),
  sidan `/app/admin` + `admin.html` (statistik + tabell över användare med rolltoggle, klientguard
  via 403). Tester `test_i18n.py` (11) + `test_admin.py` (10). Hela sviten **110 passed**, ruff/black gröna.
  Kvarstår i Fas 5: production Tailwind-bygge (just nu CDN). Locale tas från cookie (inte från
  `user.locale`) — fungerar även före login; synk med profilen — valfritt senare.
- **2026-06-07 (Fas 2 — Qasa-adapter):** `poller/sources/qasa.py` — Qasa-adapter via GraphQL
  (`api.qasa.com/graphql`, query `homes`), normalisering till `Listing` (+`fcfs`), backoff på 429/5xx,
  hantering av GraphQL-errors. ⚠️ **Kontraktet INTE verifierat** (inget officiellt publikt Qasa-API) →
  `enabled=False`, stäm av schema + ToS före aktivering. Gemensamma hjälpare `as_float/as_int` flyttade
  till `poller/sources/base.py` (återanvänds av HomeQ+Qasa). **En latent bugg fixad:**
  `poller/sources/__init__.py` importerar nu de konkreta adaptrarna → `@register` fungerar
  i prod (tidigare var registret tomt vid `python -m poller.main`). Tester `tests/test_qasa_adapter.py`
  (9) + uppdaterad `test_sources.py`. Hela sviten **89 passed**, ruff/black gröna.
- **2026-06-07 (Fas 2 — matchning + köläggning av aviseringar):** `poller/matcher.py` implementerad
  (`matches()` — only_fcfs/sources/intervall för pris-rum-yta/områdes-substräng; `match_users()`
  — grov sållning av aktiva filter i Mongo + exakt kontroll i Python). `poller/engine.py` utvidgad:
  `process_new_listings` sätter nu annonsens `_id`; ny `enqueue_notifications()` —
  matchning av nya FCFS mot filter och **idempotent** köläggning av `notifications` (status=queued,
  leverans/latency — Fas 3). Tillagt unikt index `notifications (user_id, listing_id)`
  (`uniq_user_listing`) i `shared/db.py`. Loopen `poller/main.py` anropar enqueue efter engine.
  Detta blåser liv i webbflödet `/api/listings?matched` och SSE (Change Stream på notifications) **utan Telegram**.
  Tester `tests/test_matcher.py` (12). Hela sviten **80 passed**, ruff/black gröna.
  Gren `feature/phase2-homeq-adapter`. ⚠️ Verklig polling väntar fortfarande på att adaptern aktiveras (konto+ToS).
- **2026-06-07 (Fas 2 — verklig HomeQ-adapter):** Kontraktet för HomeQ Core API avstämt mot dokumentationen
  (`docs-core.homeq.se`/`api.homeq.se`) och implementerat i `poller/sources/homeq.py`: auth
  `POST /api/v2/tokens/` (JWT, omlogin vid 401), Card Search `POST /api/v3/cards/` med
  `first_come_first=true/queue_points=false` (FCFS-only på källan), normalisering av kortet →
  fält i `Listing` (+ `fcfs` för detektorn), vidareföring av 429/5xx (Retry-After) för backoff-loopen.
  Inställningar i `shared/config.py` (`homeq_base_url`/`homeq_username`/`homeq_password`/`homeq_fetch_amount`)
  och `.env.example`. Tester `tests/test_homeq_adapter.py` på `httpx.MockTransport` (auth, search,
  normalisering, omlogin, throttling, inget konto, väg genom detektorn). Hela sviten **68 passed**,
  ruff/black gröna. Gren `feature/phase2-homeq-adapter`. ⚠️ Adaptern `enabled=False` — aktivering
  och verklig polling hos ägaren (konto från landlord-portalen + bekräftelse av ToS). Härnäst efter
  aktivering: Qasa (samma API), sedan Fas 3 (Telegram-leverans, milstolpe M2).
- **2026-06-07 (Fas 2 kärna + ToS-research):** Pollerns kärna klar (FCFS-detektor, dedup, engine,
  async-loop med adaptiv frekvens/backoff) — gren `feature/phase2-poller`, tester **58 passed**.
  ToS-research för plattformarna nedtecknad i `COMPLIANCE.md`: **HomeQ/Qasa — officiellt Core API** (prioritet),
  övriga — partnerskap/kontroll. Adaptrarna fortfarande `enabled=False` (inga nycklar/ToS-bekräftelse).
  Verklig integration av HomeQ API (Card Search/webhooks) — nästa steg efter att nyckel erhållits.
  ⚠️ Detta är en teknisk sammanfattning, inte juridisk rådgivning — beslutet om aktivering ligger hos ägaren.
- **2026-06-07 (Fas 6 + CI vaknade):** Real-time klart: `web/sse/` (broker + Change Stream watcher +
  `/sse/feed`), dashboard på `EventSource` (dedup, auto-reconnect, live-indikator, fallback polling).
  Tester **51 passed**. CI på GitHub **grön** (billing upplåst). UI-språk fastställt —
  **svenska prioriterat** (produkt för den svenska marknaden), engelska sekundärt (i18n framöver).
  Gren `feature/phase6-sse`. Härnäst: i18n (sv/en), admin-UI, eller Fas 2 (poller — ToS-blockerad).
- **2026-06-07 (Fas 5):** Frontend på Jinja2 + **Tailwind** (Play CDN) + Vanilla JS.
  `web/views.py` (sidor), `web/templates/*` (base/app_base + landing/login/register/dashboard/
  filters/notifications/settings), `web/static/js/api.js` (klient: tokens i localStorage, auto-refresh,
  guard, toast). Tillagd roll `UserRole` (user/admin) i modellen + i `/api/me`; admin-post i navigeringen
  efter roll. `frontend-build/` — config för production Tailwind-bygget (än så länge CDN). Tester **48 passed**.
  Gren `feature/phase5-frontend`. Härnäst: Wiki (manualer), sedan i18n / SSE (Fas 6) / admin-UI.
- **2026-06-07 (Fas 4 avslutad):** Alla endpoints i Fas 4 klara och mergade till `develop` (pushat).
  Tillagda: `/api/listings` (matched + paginering), `/api/notifications` (paginering),
  `/api/telegram/link|status`, OpenAPI (`web/openapi.py` → `/openapi.json`, Swagger UI `/apidocs`).
  Paginering: `?page=&limit=` (limit ≤ 100). Tester **39 passed**, ruff/black gröna.
  **Härnäst valfritt:** Fas 5 (Jinja2-frontend ovanpå API) eller Fas 2 (poller, kräver plattformarnas ToS).
- **2026-06-07 (Fas 4 kärna):** Gren `feature/phase4-api-auth` (från `develop`). Webb-kärnan implementerad:
  `shared/security.py` (Argon2 + JWT), `web/extensions.py` (limiter), `web/db.py` (DI av DB + serialize),
  `web/deps.py` (`require_auth`), blueprints `web/auth/routes.py` (register/login/refresh) och
  `web/api/routes.py` (CRUD filters + /me GDPR). Factory `create_app(db=, testing=)`. Tester: **34 passed**
  (auth, filters CRUD, användarisolering, GDPR-radering). Plattformar i scope: HomeQ, Qasa, Blocket,
  Bostad Direkt, Samtrygg (COMPLIANCE.md). Fas 1 mergad till `develop` och pushad.
  ⚠️ flask-limiter använder i dev in-memory storage (för multi-process behövs en backend; Fas 8/10).
- **2026-06-07 (ännu senare):** **Fas 1 klar** på grenen `feature/phase1-data-layer` (från `develop`).
  `shared/models.py` (alla kollektioner, multi-source, StrEnum), `shared/db.py` (`ensure_indexes`,
  sammansatt unikt `(source, external_id)`, TTL), multi-source-stomme `poller/sources/`
  (`SourceAdapter` + register + HomeQ-stub, alla `enabled=False`). Tillagt `email-validator`.
  Tester: 22 passed (models, index på mongomock, registry). **Pivot:** projektet → all-in-one-
  aggregator för svenska plattformar. `develop` pushad till GitHub (Fas 0). ⚠️ GitHub Actions blockerad
  (kontots billing) — CI körs inte, men config är korrekt; lokalt grönt.
- **2026-06-07 (sent):** **Fas 0 avslutad** på grenen `develop`. Stomme: `pyproject.toml`,
  venv 3.12, paketen `shared/web/poller/bot` (platshållare med TODO per fas), `tests/` (10 passed),
  pre-commit (ruff/black/detect-secrets + baseline), CI `ci.yml`, README/COMPLIANCE/CONTRIBUTING/LICENSE.
  `web/app.py` → `/health`. Mall-`main.py` borttagen. **Härnäst: Fas 1** (MongoDB: `shared/db.py`
  ensure_indexes + `shared/models.py`). För Fas 2 krävs ToS för HomeQ (§6 p.1 — blockerare).
- **2026-06-07:** Skapade CLAUDE.md, git/Pages, demot publicerat (alshfu.github.io/HQRTM/).

### Beslutslogg (lägg till, skriv inte om)
- **2026-06-10:** **Ny bidragsgivare: Pushkinho (Petros)** — `Petros@maktic.se`. Tillagd i
  `CONTRIBUTING.md` (avsnitt «Bidragsgivare»), `docs/wiki/Developer-Guide.md` (speglat till GitHub
  Wiki) och `pyproject.toml` (`[project].authors`). Samma person som prod-testkontot `petros`.
- **2026-06-08:** **Autoclicker/autoansökan avböjd.** Att bygga en bot som loggar in på användarnas
  plattformskonton och automatiskt skickar in ansökningar i autonomt läge byggs INTE: det strider mot
  HomeQ/Schibsten ToS, kräver lagring av tredjepartslösenord och bär juridisk risk — och motsäger
  projektets egen scope (CLAUDE.md §1, COMPLIANCE.md) och de villkor som publicerats (`/terms`).
  Legal motsvarighet som levererats: **ett-tryck-ansökan** (avisering + direktlänk till källans annons)
  + **ansökningsprofil** (snabb inklistring). Riktig autoansökan vore endast möjlig via HomeQ:s
  officiella partner-API med uttryckligt samtycke per åtgärd (kräver partnerskap — ägaråtgärd).
- **2026-06-08:** **Språk: allt på svenska.** Enligt ägarens beslut skrivs ALLA filer och dokument i projektet
  (UI, skyltfönster, demo, Wiki, CLAUDE.md, kommentarer/docstrings i koden, sample-innehåll)
  **på svenska**. Undantag — **kommunikationen i chatten med ägaren förblir på ryska** (§8). Översättning av
  den befintliga basen — stegvis, med commit/push vid varje steg.
- **2026-06-08:** **Huvudregel för processen:** vid varje avslutat steg — committa, pusha,
  uppdatera Wiki (utan separat förfrågan). Upphäver det tidigare ”pusha bara på begäran”.
- **2026-06-08:** **Verklig data + förstakälla, INGEN fiktion.** Användarytorna visar verklig
  parserdata (titel, hyra, rum, yta, **bild**, **beskrivning**) och ger alltid en länk till
  förstakällan (`Listing.url`). Tidigare fiktiva fixturer borttagna — inga påhittade annonser.
- **2026-06-08:** **HomeQ Card Search är PUBLIKT tillgänglig** (`POST api.homeq.se/api/v3/cards/`
  svarar utan JWT — samma data som webbplatsens inloggningsfria sökning). Skyltfönstret fylls med
  **riktiga Göteborg-annonser** via `HomeQAdapter.fetch_public_cards(bbox=…)` (geo-filter klientsidigt;
  API:ets shape-filter odokumenterat). Detta är en **explicit ägar-godkänd engångshämtning av publik
  data** via `scripts/gen_sample_listings.py` — **inte** 24/7-polling: adaptern är kvar `enabled=False`
  (kontinuerlig bevakning + landlord-JWT gated på ToS, COMPLIANCE.md).
- **2026-06-08:** **Telegram-leverans (Fas 3) — uppskjuten** (deferred). ~~Aviseringar bara i
  webbflödet (SSE).~~ → **Återupptagen 2026-06-08** (se nedan): boten är implementerad.
- **2026-06-08:** **Fas 3 implementerad (Telegram åter i scope för beta).** Ägaren vill koppla
  registrerade användare till boten. `bot/service.py` (koppling via engångskod + leverans av köade
  aviseringar, testbar utan aiogram), `bot/handlers.py` (aiogram `/start <kod>`), `bot/main.py`
  (long-polling + leveransloop, sätter latency_ms/delivered). Kräver `TELEGRAM_BOT_TOKEN` (BotFather)
  + en alltid-på-process. **Integritetspolicy + villkor** (`/privacy`, `/terms`, svenska, GDPR)
  klara och länkade från registreringen.
- **2026-06-07:** Stack: **Python 3.12**, **MongoDB Atlas free-tier**, licens **MIT**.
  Beroenden och tooling — i `pyproject.toml` (`[project]` + `[project.optional-dependencies]`).
  `docker-compose` uppskjutet till Fas 10 (Atlas för dev, lokal Docker krävs inte).
- **2026-06-07:** **Pivot till multi-source-aggregator** (på ägarens förslag). Källan —
  via adaptrar `poller/sources/` (`SourceAdapter` + register). En annons blev unik via
  `(source, external_id)`. Kandidatplattformar i `COMPLIANCE.md`; den slutgiltiga uppsättningen — hos ägaren.
  ToS kontrolleras per-source, adaptern aktiveras först därefter.
- **2026-06-07:** Roadmap erkänd som kanonisk stack (Flask + MongoDB + SSE + Vanilla JS).
  Dokumenten Backend/Frontend ToR — kravkällor, men deras teknologier (FastAPI/Postgres/Redis/React)
  används inte.
- **2026-06-07:** Repot — **public** (enligt GH-001), namn `HQRTM`, konto `alshfu`.
  GitHub Pages levereras från grenen `main` / roten; `index.html` i roten = skyltfönster, demot ligger i
  `HQRTM-Demo/`. Vid byte av Pages-upplägg (t.ex. till `/docs` eller `gh-pages`) — uppdatera sökvägarna och denna punkt.
