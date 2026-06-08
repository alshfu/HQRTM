# Teknisk kravspecifikation + Roadmap
## Projekt: HomeQ Real-Time Monitor (HQRTM)
### Stack: Flask · MongoDB · HTML/CSS/JS · Tailwind CSS / Bootstrap · GitHub (Public Repo + Pages + Wiki)

---

## 0. Introduktion

### 0.1 Syfte
Tjänsten bevakar HomeQ-publiceringar dygnet runt, lyfter omedelbart fram annonser av typen «Först till kvarn» (FCFS — först till kvarn, först till mölla), sållar bort kö-annonser, matchar dem mot användarnas filter och levererar en avisering med länk till Telegram inom ≤ 1.5 s. Webbgränssnittet (panelen) låter användaren själv ställa in filter, koppla Telegram och se ett levande flöde av matchningar.

### 0.2 Fastställd stack
| Lager | Teknologi |
|---|---|
| Backend API + Web | **Flask 3.x** (Python 3.12+), Jinja2-mallar |
| Poller / worker | **Separat asyncio-process**: `httpx` + `asyncio` (+ `Playwright` som fallback) |
| Telegram | `aiogram` (async) |
| Databas | **MongoDB** (PyMongo för Flask, Motor för async-worker) |
| Real-time | **MongoDB Change Streams + SSE** (eller Flask-SocketIO) |
| Frontend-stilar | **Tailwind CSS** eller **Bootstrap 5** (val — §7) |
| Frontend-logik | Vanilla **JavaScript** (`fetch`, `EventSource`) |
| Repository | **GitHub — public** |
| Demo / skyltfönster | **GitHub Pages** (statisk build med mock-data) |
| Dokumentation | **GitHub Wiki** |
| CI/CD | GitHub Actions |
| Containerisering / deploy | Docker + docker-compose på VPS, Nginx + TLS |

### 0.3 Ordlista
| Term | Betydelse |
|---|---|
| **FCFS / «Först till kvarn»** | Annons av typen «först till kvarn — först till mölla» (målobjektet). |
| **Kö-objekt** | Kö-lägenhet (efter poäng/tid) — **utesluts** av filtret. |
| **Poller / Monitoring Engine** | Separat async-process som pollar HomeQ. |
| **Dispatcher** | Utskick av aviseringar (Telegram). |
| **Change Stream** | MongoDB-mekanism för att reagera på ändringar i kollektioner i realtid. |
| **SSE** | Server-Sent Events — enkelriktat flöde server → webbläsare. |

### 0.4 Tekniska förbehåll kring stacken (viktigt!)
1. **Flask är synkront (WSGI).** Högfrekvent polling 24/7 kan inte hållas i Flask-handlers. Pollern är en **separat långlivad process** på `asyncio`. Flask ansvarar endast för API och webbgränssnitt. Kommunikation — via MongoDB.
2. **GitHub Pages — endast statiskt.** Levande Flask kan inte deployas dit. På Pages publiceras en **statisk demo-build av frontend med mock-data** (skyltfönster + dokumentation); den fungerande backenden ligger på VPS.
3. **Public Repo ⇒ inga hemligheter i koden.** Telegram-token, Mongo URI, JWT-secret osv. — **endast** via `.env` (i `.gitignore`) och **GitHub Secrets**. Inte en enda hemlighet i commit-historiken.
4. **Real-time utan Redis.** Vi använder MongoDB Change Streams (kräver MongoDB i läget replica set; i MongoDB Atlas påslaget som standard, för self-hosted — konfigurera).

### 0.5 Compliance (obligatoriskt före start)
- **ToS HomeQ + `robots.txt`:** kontrollera, dokumentera i `COMPLIANCE.md`. Officiellt API — i prioritet; scraping — fallback och endast om det inte strider mot ToS.
- **GDPR (EU):** rättslig grund, integritetspolicy, rätt till radering av data, kryptering av hemligheter, samtyckesjournal.
- **Etisk belastning:** en central poller för alla, rimliga intervall, backoff, reaktion på `429/503`.
- **Utanför scope:** boten loggar inte in på HomeQ-konto och skickar inga ansökningar — den aviserar endast.

---

## 1. Lösningsarkitektur

```
                          ┌──────────────────────────┐
                          │       HomeQ (källa)       │
                          └─────────────▲─────────────┘
                                        │ polling (1 gång för alla)
        ┌───────────────────────────────┴───────────────────────────────┐
        │              POLLER (asyncio-process, separat container)        │
        │   HomeQAdapter → FCFS Detector → Filter Matcher → Dispatcher    │
        └───────┬───────────────────────────────────────────┬────────────┘
                │ skriver listings / notifications           │ Telegram
        ┌───────▼────────────┐                       ┌───────▼────────────┐
        │      MongoDB        │◄──── Change Stream ───│   Telegram Bot     │
        │ users / filters /   │                       │   (aiogram)        │
        │ listings / notif.   │                       └────────────────────┘
        └───────▲────────────┘
                │ PyMongo
        ┌───────┴────────────────────────────────┐
        │        FLASK (API + Web, Jinja2)         │──── SSE/SocketIO ───► Webbläsare
        │  auth · filters · listings · /ws/feed    │                       (live feed)
        └──────────────────────────────────────────┘
```

**Processer (separata containrar i docker-compose):**
1. `poller` — asyncio: polling, FCFS-detektering, matchning, köläggning av aviseringar.
2. `bot` — Telegram-bot (kan ingå i `poller` eller vara separat).
3. `web` — Flask (API + webbgränssnitt + SSE).
4. `mongo` — MongoDB (replica set för Change Streams).

> Varför pollern är separat: låg latens och kontinuerlig async-loop är oförenliga med Flasks request-response-modell. Uppdelningen gör det också möjligt att skala web och poller oberoende av varandra.

---

## 2. Repository-struktur

```
hqrtm/
├── README.md                  # Quickstart, start/stopp, inställning av frekvens
├── COMPLIANCE.md              # Slutsatser om ToS HomeQ + GDPR
├── LICENSE
├── CONTRIBUTING.md
├── .gitignore                 # .env, __pycache__, node_modules, dist/ ...
├── .env.example               # Mall för variabler (utan hemlighetsvärden)
├── docker-compose.yml
├── pyproject.toml / requirements.txt
│
├── poller/                    # Async-worker
│   ├── main.py                # Ingångspunkt (asyncio loop)
│   ├── homeq_adapter.py       # Hämtning + normalisering av HomeQ-data
│   ├── detector.py            # Logik FCFS vs kö
│   ├── matcher.py             # Matchning mot filter
│   ├── dispatcher.py          # Köläggning/utskick av aviseringar
│   └── config.py
│
├── bot/                       # Telegram-bot (aiogram)
│   ├── main.py
│   └── handlers.py            # /start, koppling, test-avisering
│
├── web/                       # Flask
│   ├── app.py                 # Applikationsfabrik, blueprints
│   ├── config.py
│   ├── auth/                  # Registrering/inloggning (blueprint)
│   ├── api/                   # REST endpoints (blueprint)
│   ├── sse/                   # SSE / Change Stream listener
│   ├── templates/             # Jinja2 (base.html, dashboard.html, ...)
│   └── static/                # Kompilerad CSS, JS, ikoner
│
├── shared/
│   ├── db.py                  # Anslutning till MongoDB, index
│   └── models.py              # Scheman/validering av dokument (pydantic)
│
├── frontend-build/            # Tailwind/Bootstrap-build (input.css, config)
│
├── demo/                      # Statisk build för GitHub Pages (mock-data)
│   ├── index.html
│   ├── assets/
│   └── mock-data.js
│
├── tests/                     # unit / integration / e2e
└── .github/
    └── workflows/             # ci.yml, deploy-pages.yml, deploy-vps.yml
```

---

## 3. MongoDB-datamodell

**Kollektioner och nyckelindex:**

```javascript
// users
{ _id, email (unique idx), password_hash, telegram_chat_id,
  link_code, status, locale, consent_at, created_at }

// filters
{ _id, user_id (idx), name, city, district, rent_min, rent_max,
  rooms_min, rooms_max, area_min, area_max, only_fcfs:true, is_active, created_at }

// listings
{ _id, external_id (UNIQUE idx), title, address, district, rooms,
  area_m2, rent, listing_type, url, published_at, fetched_at (TTL idx, t.ex. 7 dagar) }

// notifications
{ _id, user_id (idx), listing_id, channel:"telegram",
  status, sent_at, latency_ms, error }

// seen_listings   (deduplicering)
{ _id: external_id, seen_at (TTL idx, t.ex. 24 h) }

// audit_log
{ _id, actor, action, payload, created_at }
```

**Datakrav:**
| ID | Krav |
|---|---|
| DB-001 | `external_id` är unikt — garanterar att en annons behandlas en gång. |
| DB-002 | TTL-index på `seen_listings.seen_at` auto-rensar gamla dedup-poster (istället för Redis). |
| DB-003 | TTL-index på `listings.fetched_at` för auto-rensning av föråldrade annonser. |
| DB-004 | Lösenord — endast hash (Argon2/bcrypt); hemligheter lagras inte i klartext. |
| DB-005 | `notifications.latency_ms` (publish → delivered) skrivs för SLA-rapportering. |
| DB-006 | MongoDB körs som replica set (minst single-node RS) för att Change Streams ska fungera. |

---

## 4. Funktionella krav

### 4.1 Poller / Monitoring Engine
| ID | Krav |
|---|---|
| BE-DE-001 | Hämtning av HomeQ-annonser via API (prioritet) eller scraping (fallback, `Playwright`). |
| BE-DE-002 | Polling är **centraliserad** — en gång per cykel, oberoende av antalet användare. |
| BE-DE-003 | Pollingintervallet är konfigurerbart (`POLL_INTERVAL_MS`), säkert standardvärde; beskrivs i README. |
| BE-DE-004 | Adaptiv frekvens: ökad takt under «heta» timmar, långsammare på natten. |
| BE-DE-005 | Parsern är isolerad i `HomeQAdapter`; vid ändring av källan justeras endast den. |
| BE-DE-006 | Normalisering till en enhetlig dokumentmodell `listings`. |

### 4.2 Detektering och filtrering
| ID | Krav |
|---|---|
| BE-FL-001 | Detektering FCFS vs kö (`detector.py`), täckt av tester. |
| BE-FL-002 | Endast **FCFS** går vidare; kö-annonser sållas bort direkt. |
| BE-FL-003 | Deduplicering via `seen_listings` + unique-index. |
| BE-FL-004 | Matchning mot filter: stad/distrikt, pris, rum, yta, `only_fcfs`. |
| BE-FL-005 | Effektiv matchning (MongoDB-query med index), utan att överskrida latensbudgeten. |

### 4.3 Aviseringar (Telegram)
| ID | Krav |
|---|---|
| BE-NT-001 | Meddelande: rubrik, distrikt, pris, rum, yta + **direktlänk** till annonsen. |
| BE-NT-002 | Parallellt utskick till alla matchande användare (async). |
| BE-NT-003 | Throttling enligt Telegram Bot API:s gränser. |
| BE-NT-004 | Återförsök med backoff; statusar skrivs till `notifications`. |
| BE-NT-005 | Koppling via deep-link/bekräftelsekod (används även av panelen). |

### 4.4 Flask API
| ID | Endpoint | Syfte |
|---|---|---|
| BE-API-001 | `POST /auth/register`, `/auth/login`, `/auth/refresh` | Registrering/inloggning (JWT). |
| BE-API-002 | `GET/POST/PUT/DELETE /api/filters` | CRUD för filter. |
| BE-API-003 | `GET /api/listings?matched=true` | Flöde av matchade annonser. |
| BE-API-004 | `GET /api/notifications` | Historik (paginering). |
| BE-API-005 | `POST /api/telegram/link`, `GET /api/telegram/status` | Koppling/status för Telegram. |
| BE-API-006 | `GET/PUT/DELETE /api/me` | Profil; radering av konto och data (GDPR). |
| BE-API-007 | `GET /sse/feed` | SSE-flöde av nya matchningar. |
| BE-API-008 | `GET /health`, `/metrics` | Health-check och metrik. |
| BE-API-009 | — | OpenAPI/Swagger (flasgger / apispec). |

### 4.5 Webbgränssnitt (skärmar)
| ID | Skärm / krav |
|---|---|
| FE-001 | Landing + registrering/inloggning. |
| FE-002 | Onboarding: koppling av Telegram (deep-link/kod) + skapande av första filtret. |
| FE-003 | Hantering av filter (CRUD, på/av, klientvalidering av intervall). |
| FE-004 | Dashboard med **levande flöde** av matchningar (SSE), kort + knapp för att gå till HomeQ. |
| FE-005 | Aviseringshistorik (paginering, filtrering). |
| FE-006 | Kontoinställningar: profil, lösenordsbyte, radering av data (GDPR). |
| FE-007 | Responsivitet (mobile-first), a11y, lokalisering (sv./eng.). |
| FE-008 | Lägen för laddning/fel/tomt på alla skärmar; auto-reconnect SSE. |

---

## 5. Icke-funktionella krav + latensbudget
| ID | Krav | Mål |
|---|---|---|
| NFR-001 | Latens publish → leverans | ≤ **1.5 s** (mål ≤ 1.0 s) |
| NFR-002 | Tillgänglighet | ≥ 99.5% / månad |
| NFR-003 | Utskickskapacitet | ≥ hundratals/min utan degradering av polling |
| NFR-004 | Skalbarhet | central polling oförändrad när användarantalet växer |
| NFR-005 | Återhämtning | autoomstart av processer, utan förlust av dedup |
| NFR-006 | Säkerhet | TLS, lösenordshash, hemligheter utanför repot, ingen PII i loggar |

**Latensbudget (mål 1.5 s):** polling ~0.5–0.8 s · request+parsing ~0.2–0.3 s · detektering+matchning ~0.05–0.15 s · utskick till Telegram ~0.2–0.4 s.

---

## 6. Frontend: Tailwind CSS vs Bootstrap
| Kriterium | Tailwind CSS | Bootstrap 5 |
|---|---|---|
| Ansats | Utility-first, anpassad design | Färdiga komponenter |
| Starthastighet | Något långsammare (kräver build) | Mycket snabbt (CDN) |
| UI-unikhet | Hög | Medel (igenkännbart «bootstrap-utseende») |
| Bundle-storlek | Liten (purge av oanvänt) | Större direkt ur lådan |
| Inlärningskurva | Något högre | Låg |

**Rekommendation:** om ett anpassat modernt utseende är viktigt och det finns tid för ett build-steg — **Tailwind** (via CLI/PostCSS; för prototyp är Play CDN acceptabelt). Om prioriteten är hastighet och färdiga komponenter — **Bootstrap 5** (CDN, minimal konfiguration). Valet fastställs i början av §Roadmap, fas 5.

**UI-struktur:** basmall `base.html` (header/navigering/footer) → ärvda sidor; gemensam designtoken (färger, typografi); komponenter för annonskort, filterformulär, toast-aviseringar.

---

## 7. Real-time-strategi
1. Pollern skriver en ny matchning till `notifications`.
2. Flask lyssnar på **Change Stream** för kollektionen `notifications` (bakgrundsflöde).
3. Vid en händelse skickar Flask data till webbläsaren via **SSE** (`/sse/feed`), filtrerat på `user_id`.
4. Klienten (`EventSource`) lägger till ett kort i flödet utan omladdning; vid avbrott — auto-reconnect.
5. Fallback: om SSE inte är tillgängligt — periodisk `GET /api/listings?matched=true`.

> Alternativ — Flask-SocketIO (dubbelriktad kanal). SSE är enklare och tillräckligt för ett enkelriktat flöde.

---

## 8. GitHub: repository, grenar, CI/CD
| ID | Krav |
|---|---|
| GH-001 | **Public** repository; `LICENSE`, `README`, `CONTRIBUTING`, `.gitignore`. |
| GH-002 | Grenstruktur: `main` (stabil) ← `develop` ← `feature/*`; PR + granskning. |
| GH-003 | Hemligheter — **endast** i GitHub Secrets och lokal `.env`; `.env` i `.gitignore`. |
| GH-004 | Pre-commit-hooks (ruff/black, detect-secrets) — skydd mot läckage av token i public repo. |
| GH-005 | CI (`ci.yml`): lint + tester på varje PR. |
| GH-006 | CD (`deploy-pages.yml`): build av demo → GitHub Pages. |
| GH-007 | CD (`deploy-vps.yml`): deploy av containrar till VPS (per tag/release). |
| GH-008 | Issues + Projects (kanban) för att spåra roadmap-uppgifter. |

---

## 9. GitHub Pages: vad vi publicerar
**Endast statiskt** — demo-skyltfönster för intressenter (den levande backenden förblir på VPS):
| ID | Krav |
|---|---|
| GP-001 | Statisk build av frontend från `demo/` med **mock-data** (`mock-data.js`). |
| GP-002 | Demonstrerar: dashboard, flöde, filterformulär, Telegram-kopplingsskärm — utan riktigt API. |
| GP-003 | Kan kompletteras med en gallerisida med exempel på aviseringar (skärmdumpar). |
| GP-004 | Publicering automatisk via Actions (grenen `gh-pages` eller katalogen `/docs`). |
| GP-005 | Länk till demo — i `README` och i Wiki. |
| GP-006 | På demon — en banner «Demo med mock-data, inte en fungerande tjänst». |

---

## 10. GitHub Wiki: sidstruktur
| Sida | Innehåll |
|---|---|
| **Home** | Projektöversikt, länkar till nyckelsidor och demo. |
| **Architecture** | Diagram, beskrivning av processer (poller/web/bot/mongo). |
| **Setup & Installation** | Lokal körning: Python, MongoDB (RS), `.env`, frontend-build. |
| **Configuration** | Alla miljövariabler, hur man ändrar pollingfrekvens. |
| **Data Model** | MongoDB-kollektioner, index, dokumentexempel. |
| **FCFS Detection** | Hur «Först till kvarn» avgörs, gränsfall. |
| **API Reference** | Endpoints, requests/responses (med länk till Swagger). |
| **Frontend Guide** | Build av Tailwind/Bootstrap, mallstruktur, SSE. |
| **Deployment (VPS)** | Docker, Nginx, TLS, backuper, start/stopp. |
| **GitHub Pages Demo** | Hur skyltfönstret byggs och publiceras. |
| **Troubleshooting / FAQ** | Vanliga problem (källa otillgänglig, SSE bryts osv.). |
| **Compliance & Legal** | ToS HomeQ, GDPR, begränsningar (utanför scope). |
| **Roadmap & Changelog** | Framsteg per fas, versionshistorik. |

---

## 11. ROADMAP — stegvis implementering
> Checklistor kan föras direkt i Issues/Projects. Tidsangivelser är ungefärliga (för 1 utvecklare); med ett team — parallelliseras.

### Fas 0 — Förberedelse (≈ 2–3 dagar)
- [ ] Skapa **public** repository, lägg till `LICENSE`, `README`, `.gitignore`, `CONTRIBUTING.md`.
- [ ] Sätta upp katalogstrukturen (se §2).
- [ ] Konfigurera virtuell miljö, `requirements.txt`/`pyproject.toml`.
- [ ] Skapa `.env.example`; konfigurera inläsning av `.env` (python-dotenv); lägga till `.env` i `.gitignore`.
- [ ] Koppla in pre-commit (ruff/black + **detect-secrets**) — skydd av public repo mot läckage.
- [ ] Initiera **Wiki** med ett skelett av sidor (§10, tills vidare platshållare).
- [ ] Konfigurera CI `ci.yml` (lint + tom testkörning).
- [ ] Skapa ett GitHub Project (kanban) och flytta roadmap-stegen till Issues.

### Fas 1 — MongoDB-datalager (≈ 2–3 dagar)
- [ ] Sätta upp MongoDB lokalt som **replica set** (för Change Streams) och/eller skapa Atlas free-tier.
- [ ] `shared/db.py`: anslutning (PyMongo + Motor), funktion för att skapa index.
- [ ] Skapa kollektioner och index (unique `external_id`, TTL `seen_listings`, TTL `listings`).
- [ ] `shared/models.py`: pydantic-scheman och validering av dokument.
- [ ] Wiki: fylla i **Data Model**.

### Fas 2 — Poller / PoC (≈ 1 vecka) → **Milstolpe M1**
- [ ] Undersöka HomeQ-källan (API vs scraping), dokumentera i `COMPLIANCE.md`.
- [ ] `homeq_adapter.py`: hämtning + normalisering till modellen `listings`.
- [ ] `detector.py`: logik FCFS vs kö + unit-tester på gränsfall.
- [ ] Deduplicering via `seen_listings`.
- [ ] `poller/main.py`: async-pollingloop med backoff och adaptiv frekvens.
- [ ] **Kontroll M1:** FCFS-annonser detekteras stabilt, kö-annonser sållas bort.
- [ ] Wiki: **FCFS Detection**.

### Fas 3 — Telegram-integration (≈ 4–5 dagar) → **Milstolpe M2**
- [ ] Skapa en bot via BotFather; token — i `.env`/Secrets (inte i koden!).
- [ ] `bot/handlers.py`: `/start`, koppling via deep-link/kod, test-avisering.
- [ ] `matcher.py`: matchning av annons mot användarnas filter (MongoDB-query).
- [ ] `dispatcher.py`: async-utskick, throttling, retry, skrivning till `notifications` + `latency_ms`.
- [ ] **Kontroll M2:** testaviseringar kommer fram med korrekta data och länk.

### Fas 4 — Flask API + Auth (≈ 1 vecka)
- [ ] `web/app.py`: applikationsfabrik, blueprints, konfiguration.
- [ ] Auth: registrering/inloggning, lösenordshash (Argon2/bcrypt), JWT (access+refresh) eller sessioner.
- [ ] Rate-limiting på auth (flask-limiter).
- [ ] CRUD `/api/filters`.
- [ ] `/api/listings`, `/api/notifications` (paginering).
- [ ] `/api/telegram/link`, `/api/telegram/status`.
- [ ] `/api/me` (GET/PUT/DELETE — radering av data GDPR).
- [ ] OpenAPI/Swagger (flasgger).
- [ ] Wiki: **API Reference**, **Configuration**.

### Fas 5 — Frontend (Flask + Tailwind/Bootstrap + JS) (≈ 1.5 veckor)
- [ ] **Fastställa valet: Tailwind eller Bootstrap**; konfigurera build (eller CDN).
- [ ] `base.html` + designtoken + navigering/footer.
- [ ] Auth-sidor (registrering/inloggning) med validering.
- [ ] Onboarding + UI för Telegram-koppling (status, test-avisering).
- [ ] UI för filterhantering (CRUD, på/av, validering av intervall).
- [ ] Dashboard + **levande flöde** (SSE/`EventSource`) + annonskort.
- [ ] Aviseringshistorik (paginering, filter).
- [ ] Kontoinställningar (profil, lösenord, radering av data).
- [ ] Responsivitet (mobile-first), a11y, i18n (sv./eng.), lägen för laddning/fel/tomt.
- [ ] Wiki: **Frontend Guide**.

### Fas 6 — Real-time (SSE + Change Streams) (≈ 3–4 dagar)
- [ ] Bakgrundslyssnare för Change Stream på kollektionen `notifications` i Flask.
- [ ] Endpoint `/sse/feed` med filtrering på `user_id`.
- [ ] Klientens `EventSource` + dedup + auto-reconnect; fallback till polling.
- [ ] Test av anslutningsavbrott och återhämtning.

### Fas 7 — GitHub Pages demo (≈ 2–3 dagar)
- [ ] Bygga en statisk version av frontend i `demo/` med `mock-data.js`.
- [ ] Lägga till en banner «Demo / mock-data».
- [ ] Konfigurera `deploy-pages.yml` (Actions → `gh-pages`/`/docs`).
- [ ] Kontrollera publiceringen, lägga till länk i `README` och Wiki.
- [ ] Wiki: **GitHub Pages Demo**.

### Fas 8 — Robusthet, säkerhet, observerbarhet (≈ 4–5 dagar)
- [ ] Felhantering + circuit breaker i pollern; reaktion på `429/403`.
- [ ] Larm till administratör (Telegram/e-post) vid fel i källa/utskick/ökad latens.
- [ ] Anti-blocking inom ToS: rotation av User-Agent, jitter på intervall, respekt för `Retry-After`.
- [ ] Strukturerad loggning (utan PII), `/health`, `/metrics`.
- [ ] Graceful degradation vid ändring av HomeQ-markup (larm, utan krasch).

### Fas 9 — Testning (≈ 1 vecka)
- [ ] Unit: `detector`, `matcher` (inklusive gränsfall).
- [ ] Integration: API + MongoDB (`mongomock` eller test-container).
- [ ] Deduplicering och idempotens.
- [ ] E2E (Playwright): registrering → koppling av Telegram → skapande av filter → matchning i flödet.
- [ ] Belastning (locust): tillväxt av användare vid oförändrad central polling.
- [ ] Mätning av verklig latens på testdata.

### Fas 10 — Utrullning på VPS (≈ 4–5 dagar) → **Milstolpe M3**
- [ ] Dockerfile-er för `poller`, `bot`, `web`; `docker-compose.yml` (+ `mongo` som RS).
- [ ] Provisionering av VPS; Nginx reverse proxy; TLS (Let's Encrypt/certbot).
- [ ] Restart-policy / autoomstart av processer.
- [ ] Backup av MongoDB (`mongodump` via cron).
- [ ] `deploy-vps.yml` (CI/CD-deploy per release).
- [ ] **48-timmars live-testkörning.**
- [ ] Wiki: **Deployment (VPS)**.

### Fas 11 — Dokumentation och leverans (≈ 2–3 dagar)
- [ ] Slutfylla alla Wiki-sidor (§10).
- [ ] Finalisera `README` (quickstart, start/stopp, inställning av frekvens).
- [ ] `COMPLIANCE.md`, `LICENSE`, `CONTRIBUTING.md` — final.
- [ ] Gå igenom acceptanschecklistan (§14) och Definition of Done (§15).

**Sammanfattad tidslinje (riktmärke, 1 utvecklare):** ≈ 7–9 veckor. M1 — slutet av fas 2; M2 — slutet av fas 3; M3 — slutet av fas 10.

---

## 12. Testning (sammanfattat)
Unit (detektor, matchning) · Integration (API + Mongo) · Dedup/idempotens · E2E (Playwright, hela användarflödet) · Belastning (locust) · Mätning av latens · Test «källa går sönder».

---

## 13. Säkerhet och anonymisering (inom ToS)
TLS · lösenordshash (Argon2/bcrypt) · hemligheter utanför repot (Secrets + `.env`) · detect-secrets i pre-commit · rate-limiting på auth · rotation av User-Agent · rimliga intervall och jitter · respekt för `429/Retry-After` · loggar utan PII.

---

## 14. Leveranser och acceptanskriterier
**Leveranser:**
1. Dokumenterad kod i ett **public** GitHub-repository (poller + bot + web).
2. Utrullad fungerande tjänst på VPS (24/7).
3. **GitHub Pages** — statiskt demo-skyltfönster med mock-data.
4. Komplett **GitHub Wiki**.
5. `README` (start/stopp/frekvens), `COMPLIANCE.md`, OpenAPI-dokumentation.

**Acceptanskriterier:**
- FCFS detekteras, kö-annonser sållas bort (tester + verkliga data).
- Avisering med länk kommer fram i Telegram; uppmätt latens ≤ 1.5 s.
- Panel: hela flödet registrering → Telegram → filter → levande flöde → historik.
- Tjänsten överlever nätverksfel och emulering av ändring av källan utan krasch.
- Demo publicerat på Pages, Wiki ifylld, inga hemligheter i den publika historiken.

---

## 15. Risker och Definition of Done
| Risk | Mitigering |
|---|---|
| Ändring av HomeQ-källan | Isolerad adapter, tester, larm + graceful degradation. |
| Blockering pga frekvens/IP | Central poller, rimliga intervall, backoff, `429`. |
| Läckage av hemligheter i public repo | `.gitignore`, GitHub Secrets, detect-secrets i pre-commit. |
| Flask-latens | Pollern — separat async-process; matchning via index. |
| Change Streams fungerar inte | MongoDB i läget replica set (Atlas eller RS-konfiguration). |
| GitHub Pages ≠ backend | På Pages — endast statiskt demo; fungerande backend på VPS. |
| GDPR-bristande efterlevnad | Policy, samtycken, radering av data, kryptering av hemligheter. |

**Definition of Done:** alla acceptanskriterier uppfyllda · CI grön · monitoring/larm + DB-backup konfigurerade · dokumentation (Wiki/README/COMPLIANCE/OpenAPI) aktuell · 48-timmars körning utan kritiska incidenter · inga hemligheter i den publika historiken.

---

## 16. Öppna frågor (fastställs före start)
1. HomeQ: finns officiellt/partner-API? Vad tillåter ToS?
2. Tailwind eller Bootstrap — slutgiltigt val?
3. Förväntat antal användare (belastning, val av VPS)?
4. Behövs monetisering/prisplaner och admin-panel i denna fas?
5. MongoDB: self-hosted (konfiguration av replica set) eller Atlas?
6. Gränssnittsspråk vid start (sv./eng./övriga)?
