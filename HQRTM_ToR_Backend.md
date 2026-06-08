# Teknisk specifikation (kravspecifikation) — BACKEND
## Projekt: HomeQ Real-Time Monitor (HQRTM)
### Fas 1 — serverdelen (övervakningskärna, API, infrastruktur)

> Detta är **det första av två** dokument i projektet. Det andra är `HQRTM_ToR_Frontend.md` (webbgränssnittet), som ansluter till det API som beskrivs här.

---

## 0. Allmänna bestämmelser

### 0.1 Syfte
Utveckla och driftsätta en robust servertjänst som dygnet runt bevakar HomeQ:s publiceringar, omedelbart identifierar annonser av typen «Först till kvarn» (FCFS / först till kvarn — först att få), sållar bort kö-annonser, matchar dem mot användarnas filter och levererar en avisering med länk till Telegram inom den fastställda latensbudgeten. Tjänsten tillhandahåller även ett API och datalagring för att koppla in Frontend (Fas 2).

### 0.2 Ordlista
| Term | Betydelse |
|---|---|
| **FCFS / «Först till kvarn»** | Annonstyp «först till kvarn — först att få». Det primära bevakningsobjektet. |
| **Kö-objekt** | En vanlig kö-lägenhet (efter poäng/kötid). **Exkluderas** av filtret. |
| **Latency budget** | Tillåten tid från att en annons publiceras till att aviseringen levereras. |
| **Poller / Monitoring Engine** | Tjänst som frågar HomeQ med hög frekvens. |
| **Dispatcher** | Tjänst för utskick av aviseringar. |
| **Tenant / användare** | Slutmottagare av aviseringar med sin egen uppsättning filter. |

### 0.3 Centralt arkitekturbeslut
**En central poller för alla användare** istället för N personliga botar. Detta minskar den totala lasten på HomeQ N gånger, förenklar efterlevnaden av ToS och minskar latensen (frågan utförs en gång per cykel, utskicket sker parallellt).

### 0.4 Juridiska förbehåll och compliance (obligatoriskt före start)
1. **HomeQ:s ToS.** Granska användarvillkoren och `robots.txt`; dokumentera slutsatserna i `COMPLIANCE.md`.
2. **Officiellt API i första hand.** Om HomeQ erbjuder ett offentligt/partner-API — använd det; skrapning endast som fallback och under förutsättning att det inte strider mot ToS.
3. **GDPR (EU).** Personuppgifter lagras (e-post, Telegram-ID, filter): det krävs rättslig grund, integritetspolicy, rätt till radering, kryptering av hemligheter och samtyckeslogg.
4. **Etisk last.** Rimliga intervall, exponentiell backoff, korrekt hantering av `429/503`, ingen flod från flera IP-adresser.
5. **Utanför scope:** boten **loggar inte** in på användarens konto på HomeQ och **lämnar inte** in ansökningar automatiskt — den aviserar endast.

---

## 1.1 Mål för fasen
- dygnet runt-bevakning av HomeQ med hög frekvens;
- omedelbar identifiering av FCFS och bortsållning av kö-annonser;
- matchning av en ny annons mot alla användares filter;
- leverans av en avisering till Telegram inom latensbudgeten;
- API och lagring för att koppla in Frontend (Fas 2).

## 1.2 Arkitektur
```
                         ┌─────────────────────────┐
                         │      HomeQ (källa)        │
                         └────────────▲─────────────┘
                                      │ fråga (1 gång för alla)
                         ┌────────────┴─────────────┐
                         │   Monitoring Engine       │
                         │   (poller, async)         │
                         └────────────┬─────────────┘
                                      │ nya objekt
                         ┌────────────▼─────────────┐
                         │   FCFS Detector + Filter  │
                         │   Matcher                 │
                         └──────┬─────────────┬──────┘
                                │             │
                  matchning per │             │ dedup / logg
                    filter      │             │
                         ┌──────▼──────┐  ┌───▼──────────┐
                         │ Dispatcher  │  │ PostgreSQL    │
                         │ (Telegram)  │  │  + Redis      │
                         └──────┬──────┘  └───▲──────────┘
                                │             │
                         ┌──────▼─────────────┴──────┐
                         │   API Service (REST + WS)  │◄──── Frontend (Fas 2)
                         └────────────────────────────┘
```

**Komponenter (separata processer/containrar):**
1. **Monitoring Engine** — asynkron poller för källan.
2. **FCFS Detector + Filter Matcher** — detektering av annonstyp och matchning mot filter.
3. **Notification Dispatcher** — utskick (Telegram i fas 1; e-post/push — förberedelse).
4. **API Service** — REST + WebSocket för Frontend.
5. **Data Layer** — PostgreSQL (beständiga data) + Redis (dedup, köer, rate-limit, pub/sub).
6. **Telegram Bot** — separat token, webhook eller long-polling.

## 1.3 Funktionella krav

### 1.3.1 Modul för datainsamling (Data Extraction)
| ID | Krav |
|---|---|
| BE-DE-001 | Hämta listan över HomeQ-annonser via API (prioritet) eller skrapning (fallback). |
| BE-DE-002 | Frågan utförs **centralt en gång** per cykel, oberoende av antalet användare. |
| BE-DE-003 | Frågeintervallet är konfigurerbart (`POLL_INTERVAL_MS`) med ett säkert standardvärde; beskriv i ReadMe. |
| BE-DE-004 | Adaptiv frekvens: tätare under «heta» timmar, långsammare nattetid (konfigurerbara fönster). |
| BE-DE-005 | Parsern är utbruten i en separat adapter (`HomeQAdapter`); vid ändrat kontrakt justeras endast den. |
| BE-DE-006 | Normalisering till en enhetlig modell: `external_id`, `title`, `address`, `district`, `rooms`, `area_m2`, `rent`, `listing_type`, `published_at`, `url`. |

### 1.3.2 Modul för detektering och filtrering
| ID | Krav |
|---|---|
| BE-FL-001 | Detektera annonstyp: **FCFS** vs **kö**; logiken täcks av tester. |
| BE-FL-002 | Släpp vidare **endast FCFS**; kö-annonser kasseras i ett så tidigt skede som möjligt. |
| BE-FL-003 | Deduplicering: varje annons bearbetas en gång (`external_id` i Redis med TTL). |
| BE-FL-004 | Matchning mot filter: stadsdel/stad, prisintervall, antal rum, min/max area, typ (FCFS obligatoriskt). |
| BE-FL-005 | Effektiv matchning (index/förhämtning) som inte äter upp latensbudgeten när användarantalet växer. |
| BE-FL-006 | För varje matchning skapas ett aviseringsuppdrag (user_id + listing). |

### 1.3.3 Aviseringsmodul (Telegram)
| ID | Krav |
|---|---|
| BE-NT-001 | Meddelande i Telegram: rubrik, nyckelparametrar (stadsdel, pris, rum, area) + **direktlänk**. |
| BE-NT-002 | Parallellt utskick till alla matchade användare (async, utan att blockera frågecykeln). |
| BE-NT-003 | Efterlevnad av Telegram Bot API:s begränsningar (throttling, utskickskö i Redis). |
| BE-NT-004 | Loggning av leverans/fel; misslyckade — nytt försök med backoff. |
| BE-NT-005 | Koppling av användare till Telegram via deep-link/bekräftelsekod (används även av Frontend). |
| BE-NT-006 | Utbyggbart kanalgränssnitt (`NotificationChannel`) för e-post/push utan att skriva om kärnan. |

### 1.3.4 Datalagringslager (schema, utkast)
```sql
users            (id, email, password_hash, telegram_chat_id, status, created_at, consent_at)
filters          (id, user_id FK, name, city, district, rent_min, rent_max,
                  rooms_min, rooms_max, area_min, area_max, only_fcfs, is_active)
listings         (id, external_id UNIQUE, title, address, district, rooms,
                  area_m2, rent, listing_type, url, published_at, fetched_at)
notifications    (id, user_id FK, listing_id FK, channel, status,
                  sent_at, latency_ms, error)
audit_log        (id, actor, action, payload_json, created_at)
```
| ID | Krav |
|---|---|
| BE-DB-001 | PostgreSQL för beständiga data; migreringar (Alembic). |
| BE-DB-002 | Redis för: «sedda» annonser, aviseringskö, rate-limit, pub/sub WebSocket. |
| BE-DB-003 | Tokens/hemligheter — krypterade; lösenord — endast hash (Argon2/bcrypt). |
| BE-DB-004 | Måttet `latency_ms` (publish → delivered) registreras för varje avisering (för SLA). |

### 1.3.5 API (REST + WebSocket)
| ID | Endpoint (exempel) | Syfte |
|---|---|---|
| BE-API-001 | `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh` | Registrering och autentisering (JWT). |
| BE-API-002 | `GET/POST/PUT/DELETE /filters` | CRUD för användarens filter. |
| BE-API-003 | `GET /listings?matched=true` | Flöde av matchade annonser. |
| BE-API-004 | `GET /notifications` | Aviseringshistorik med paginering. |
| BE-API-005 | `POST /telegram/link` / `GET /telegram/status` | Koppling och status för Telegram. |
| BE-API-006 | `GET /me`, `PUT /me`, `DELETE /me` | Profil; radering av konto och data (GDPR). |
| BE-API-007 | `WS /ws/feed` | Real-time push av nya matchningar till Frontend. |
| BE-API-008 | `GET /health`, `GET /metrics` | Health-check och mätvärden. |
| BE-API-009 | — | OpenAPI/Swagger-dokumentation genereras automatiskt. |

### 1.3.6 Autentisering och auktorisering
| ID | Krav |
|---|---|
| BE-AU-001 | JWT (access + refresh), återkallande av refresh-tokens. |
| BE-AU-002 | Roller: `user`, `admin`; åtkomst till andras data nekas på tjänstenivå. |
| BE-AU-003 | Rate-limiting på auth-endpoints. |
| BE-AU-004 | Valfritt: e-postbekräftelse. |

## 1.4 Icke-funktionella krav (NFR)
| ID | Krav | Målvärde |
|---|---|---|
| NFR-001 | **Latens** publish → leverans | ≤ **1,5 s** (mål ≤ 1,0 s) |
| NFR-002 | Tjänstens tillgänglighet | ≥ 99,5 % / månad |
| NFR-003 | Genomströmning vid utskick | ≥ hundratals aviseringar/min utan degradering av frågan |
| NFR-004 | Skalbarhet per användare | linjär matchningskostnad, central fråga oförändrad |
| NFR-005 | Återhämtning efter fel | autostart, utan förlust av «sedda» annonser |
| NFR-006 | Säkerhet | TLS, lösenordshash, kryptering av hemligheter, ingen PII i loggar |

**Latensbudget (uppdelning av målet 1,5 s):**
| Steg | Budget |
|---|---|
| Frågeintervall (värsta fall) | ~ 0,5–0,8 s |
| Nätverksförfrågan + parsning | ~ 0,2–0,3 s |
| FCFS-detektering + matchning + dedup | ~ 0,05–0,15 s |
| Skapande och utskick till Telegram | ~ 0,2–0,4 s |
| **Totalt (målkorridor)** | **~ 1,0–1,5 s** |

## 1.5 Robusthet och felhantering
| ID | Krav |
|---|---|
| BE-RS-001 | Retry med exponentiell backoff vid nätverksfel och `5xx`. |
| BE-RS-002 | Circuit breaker: vid en serie fel — tillfällig nedbromsning, utan krasch. |
| BE-RS-003 | Korrekt hantering av `429/403` (ökat intervall, paus). |
| BE-RS-004 | Vid ändring av HomeQ:s kontrakt — alert + graceful degradation (tjänsten kraschar inte). |
| BE-RS-005 | Health-checks + autostart (systemd/Docker restart policy). |
| BE-RS-006 | Alerter till administratören vid otillgänglig källa, ökad latens, misslyckade utskick. |
| BE-RS-007 | Idempotens: en omstart leder inte till dubblerade aviseringar. |

## 1.6 Anonymisering / skydd mot blockeringar (inom ramen för ToS)
| ID | Krav |
|---|---|
| BE-AN-001 | Korrekta/roterande User-Agent. |
| BE-AN-002 | Rimliga intervall och jitter (utan aggressiv flod). |
| BE-AN-003 | Respekt för `429/Retry-After` och backoff. |
| BE-AN-004 | (Valfritt) proxy-pool — endast om det inte strider mot ToS; målet är robusthet, inte illvillig kringgång. |

## 1.7 Teknikstack (förslag)
| Lager | Teknik | Motivering |
|---|---|---|
| Språk | Python 3.12+ | Enligt ursprunglig kravspec; mogen async-ekosystem. |
| Fråga/HTTP | `httpx` + `asyncio` | Asynkron, låg latens. |
| Skrapning (fallback) | `Playwright` | Om JS-rendering behövs. |
| API | FastAPI + Uvicorn | Async, auto-OpenAPI, WebSocket direkt ur lådan. |
| Telegram | `aiogram` / `python-telegram-bot` | Async-botar. |
| DB | PostgreSQL + SQLAlchemy + Alembic | Tillförlitlighet, migreringar. |
| Cache/köer | Redis | Dedup, rate-limit, pub/sub. |
| Containerisering | Docker + docker-compose | Reproducerbar miljö. |
| Övervakning | Prometheus + Grafana / Uptime Kuma | Mätvärden och uptime. |
| Loggar | structlog / loguru | Strukturerade loggar utan PII. |

## 1.8 Driftsättning och DevOps
| ID | Krav |
|---|---|
| BE-OPS-001 | Driftsättning på en budget-VPS, 24/7. |
| BE-OPS-002 | Alla tjänster i Docker; start via `docker-compose`. |
| BE-OPS-003 | CI/CD (GitHub Actions): lint, tester, byggande av images. |
| BE-OPS-004 | Hemligheter — via miljövariabler/secret-store, inte i repot. |
| BE-OPS-005 | Säkerhetskopiering av DB (schemalagd). |
| BE-OPS-006 | ReadMe: start, stopp, ändring av målfrekvens, återhämtning. |

## 1.9 Testning
| ID | Krav |
|---|---|
| BE-QA-001 | Unit-tester för FCFS-detektorn och filtermatchningen (inklusive gränsfall). |
| BE-QA-002 | Integrationstester av API (auth, CRUD av filter, aviseringar). |
| BE-QA-003 | Tester av deduplicering och idempotens. |
| BE-QA-004 | Lasttest: ökat antal användare med oförändrad central fråga. |
| BE-QA-005 | Mätning av verklig latens på testdata. |
| BE-QA-006 | Test av «källfel» (emulering av ändrad markup) — utan krasch, med alert. |

## 1.10 Leveranser och acceptanskriterier
**Leveranser:**
1. Dokumenterad källkod i ett privat Git-repo.
2. Driftsatt fungerande backend (poller + API + DB + bot) på överenskommen VPS.
3. `ReadMe.md` (start/stopp/frekvensinställning) + `COMPLIANCE.md`.
4. OpenAPI-dokumentation av API:t.

**Acceptanskriterier:**
- FCFS detekteras, kö-annonser sållas bort (tester + verkliga data).
- Avisering med länk kommer fram till Telegram; uppmätt latens ≤ 1,5 s under typiska förhållanden.
- Tjänsten överlever nätverksfel och emulering av en ändrad källa utan krasch.
- API:t är redo att kopplas till Frontend (auth, filter, flöde, historik, WebSocket).

## 1.11 Faser i etappen
| Fas | Innehåll |
|---|---|
| M1 — Proof of Concept | Datainsamling från HomeQ + bekräftad detektering av «Först till kvarn». |
| M2 — Integration | Telegram-boten skickar testaviseringar med korrekta data. |
| M3 — API + DB | Lagring, auth och API klara (för Frontend). |
| M4 — Driftsättning & Test | Driftsättning på VPS + 48 h live-test. |

---

## Risker (backend)
| Risk | Åtgärd |
|---|---|
| Ändring av HomeQ:s markup/kontrakt | Isolerad adapter, tester, alert + graceful degradation. |
| Blockering efter IP/frekvens | Central poller, rimliga intervall, backoff, respekt för `429`. |
| Brott mot HomeQ:s ToS | Granskning av ToS, prioritering av officiellt API, `COMPLIANCE.md`. |
| GDPR-bristande efterlevnad | Policy, samtycken, radering av data, kryptering av hemligheter. |
| Överskridande av latensbudget | Profilering, async-utskick, optimering av matchning, cache i Redis. |
| Telegram-begränsningar | Utskickskö + throttling. |

## Definition of Done (backend)
- Acceptanskriterierna uppfyllda; CI grön (lint + tester).
- Övervakning och alerter konfigurerade; DB-backup finns.
- Dokumentationen (`ReadMe`, `COMPLIANCE`, OpenAPI) aktuell.
- Live-körning ≥ 48 h utan kritiska incidenter genomförd.

## Öppna frågor
1. Erbjuder HomeQ ett officiellt/partner-API? Vad tillåter ToS?
2. Förväntat antal användare (last, VPS-kostnad)?
3. Behövs e-post/push redan i Fas 1 eller som förberedelse?
4. Krav på hostingens geografi (EU/GDPR-dataresidens)?
