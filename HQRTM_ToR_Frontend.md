# Teknisk kravspecifikation (ToR) — FRONTEND
## Projekt: HomeQ Real-Time Monitor (HQRTM)
### Etapp 2 — webbapplikation (personlig panel / dashboard)

> Detta är **det andra av två** dokument i projektet. Det första är `HQRTM_ToR_Backend.md`. Frontend **ansluter till API:t** som implementerades i Etapp 1 och duplicerar inte serverlogiken.

---

## 0. Allmänna bestämmelser

### 0.1 Syfte
Webbapplikation (personlig panel/dashboard) som låter användaren **utan inblandning av en utvecklare**: registrera sig och logga in, koppla Telegram, skapa och redigera övervakningsfilter, se ett levande flöde av matchade annonser (real-time) och historik över aviseringar samt hantera kontot. Denna etapp implementerar just det «kommersiellt gränssnitt» som i den ursprungliga kravspecifikationen låg utanför scope för den första fasen.

### 0.2 Ordlista
| Term | Betydelse |
|---|---|
| **FCFS / «Först till kvarn»** | Annonstyp «först till kvarn — först betjänad» (målet). |
| **Filter** | Uppsättning av användarens kriterier (stad/område, pris, rum, yta, «endast FCFS»). |
| **Levande flöde (feed)** | Real-time-lista över annonser som matchat filtren. |

### 0.3 Beroende av Backend
Frontend konsumerar API:t från Etapp 1. Det minimala kontraktet den förlitar sig på:
| Metod | Endpoint | Syfte |
|---|---|---|
| POST | `/auth/register`, `/auth/login`, `/auth/refresh` | Registrering/inloggning (JWT). |
| GET/POST/PUT/DELETE | `/filters` | CRUD för filter. |
| GET | `/listings?matched=true` | Flöde av matchade annonser. |
| GET | `/notifications` | Historik över aviseringar (paginering). |
| POST/GET | `/telegram/link`, `/telegram/status` | Koppling och status för Telegram. |
| GET/PUT/DELETE | `/me` | Profil och radering av konto (GDPR). |
| WS | `/ws/feed` | Real-time push av nya matchningar. |

### 0.4 Compliance (för Frontend)
- **GDPR:** skärm för radering av konto och all data (right to erasure), synliga länkar till integritetspolicy och villkor, uttryckligt samtycke vid registrering.
- Tokens/sessioner ska lagras säkert (httpOnly cookie föredras), logga inte PII i webbläsaren.

---

## 2.1 Etappens mål
Ge användaren en fullständig och självständig väg:
registrering → koppling av Telegram → konfiguration av filter → levande flöde av matchningar (real-time) → historik över aviseringar → hantering av kontot.

## 2.2 Frontendarkitektur
- **SPA** (eller SSR/Next.js för SEO-landningssida + skyddad dashboard).
- Kommunikation med backend via REST + **WebSocket** (`/ws/feed`) för real-time.
- Säker lagring av tokens och automatisk refresh av JWT.

## 2.3 Skärmkarta / användarscenarier
1. **Landing** → registrering/inloggning.
2. **Onboarding**: koppling av Telegram (deep-link/kod) → skapande av första filtret.
3. **Dashboard**: levande flöde av matchningar + snabb åtkomst till filter.
4. **Filter**: lista, skapande, redigering, på/av.
5. **Aviseringshistorik**: lista med paginering och filtrering.
6. **Kontoinställningar**: profil, lösenordsbyte, radering av konto (GDPR).
7. *(Valfritt)* **Fakturering/abonnemang**.
8. *(Valfritt)* **Adminpanel**: användare, källans status, mätvärden.

## 2.4 Funktionella krav (per skärm)

### Registrering / inloggning
| ID | Krav |
|---|---|
| FE-AU-001 | Formulär för registrering och inloggning med validering; hantering av API-fel. |
| FE-AU-002 | Lagring av session och automatisk refresh av token. |
| FE-AU-003 | Skyddade rutter (utan autentisering — omdirigering till inloggning). |

### Onboarding och koppling av Telegram
| ID | Krav |
|---|---|
| FE-TG-001 | Knapp/instruktion för koppling av Telegram (deep-link eller bekräftelsekod). |
| FE-TG-002 | Indikator för kopplingsstatus (kopplad/inte kopplad) + möjlighet att koppla bort. |
| FE-TG-003 | Testavisering «kontrollera anslutningen». |

### Hantering av filter
| ID | Krav |
|---|---|
| FE-FL-001 | CRUD för filter: stad/område, prisintervall, rum (min/max), yta (min/max), «endast FCFS». |
| FE-FL-002 | På/av för filter utan radering. |
| FE-FL-003 | Klientvalidering av intervall (min ≤ max osv.). |
| FE-FL-004 | Tips/förhandsvisning: hur många annonser som skulle matcha (om backend tillhandahåller det). |

### Levande flöde / dashboard
| ID | Krav |
|---|---|
| FE-FE-001 | Real-time-tillägg av nya matchningar via WebSocket (utan omladdning). |
| FE-FE-002 | Annonskort: nyckelparametrar + knapp för att gå vidare till HomeQ. |
| FE-FE-003 | Tillstånd: laddning, tomt, anslutningsfel (auto-reconnect WebSocket). |
| FE-FE-004 | Visuell/ljudmässig markering av en färsk matchning. |

### Aviseringshistorik
| ID | Krav |
|---|---|
| FE-HS-001 | Lista över skickade aviseringar med paginering. |
| FE-HS-002 | Filtrering efter datum/status/kanal. |
| FE-HS-003 | Visning av leveransstatus och latens (om backend tillhandahåller det). |

### Kontoinställningar
| ID | Krav |
|---|---|
| FE-ST-001 | Redigering av profil, lösenordsbyte. |
| FE-ST-002 | Radering av konto och all data (GDPR) med bekräftelse. |
| FE-ST-003 | Länkar till integritetspolicy och villkor. |

### (Valfritt) Fakturering / abonnemang
| ID | Krav |
|---|---|
| FE-BL-001 | Visning av aktuellt abonnemang och gränser. |
| FE-BL-002 | Integration av betalningsleverantör (Stripe o.d.) vid monetisering. |

### (Valfritt) Adminpanel
| ID | Krav |
|---|---|
| FE-AD-001 | Lista över användare och statusar. |
| FE-AD-002 | Källans status (HomeQ tillgänglig/inte), latensmätvärden, senaste felen. |

## 2.5 Real-time (WebSocket/SSE)
| ID | Krav |
|---|---|
| FE-RT-001 | Prenumeration på `/ws/feed` efter autentisering. |
| FE-RT-002 | Auto-reconnect med backoff vid avbrott. |
| FE-RT-003 | Deduplicering av inkommande meddelanden på klienten. |
| FE-RT-004 | Fallback till polling när WebSocket inte är möjlig. |

## 2.6 UI/UX, responsivitet, tillgänglighet, lokalisering
| ID | Krav |
|---|---|
| FE-UX-001 | Designsystem/UI-kit (komponentbibliotek), enhetlig stil. |
| FE-UX-002 | Responsivitet: mobile-first (bostadsövervakning är kritisk på telefonen). |
| FE-UX-003 | Tillgänglighet (a11y): kontrast, tangentbordsnavigering, ARIA. |
| FE-UX-004 | Lokalisering: svenska (primär) + engelska; i18n-arkitektur förberedd för fler språk. |
| FE-UX-005 | Tydliga tillstånd för laddning/fel/tom data på alla skärmar. |

## 2.7 Teknologistack (förslag)
| Lager | Teknologi |
|---|---|
| Framework | React + TypeScript (eller Next.js vid behov av SSR/landningssida) |
| State/data | TanStack Query (server state) + Zustand/Redux vid behov |
| Stilar | Tailwind CSS + komponentbibliotek (shadcn/ui o.d.) |
| Real-time | Native WebSocket / Socket.IO-klient |
| Bygge | Vite |
| Tester | Vitest/Jest + React Testing Library + Playwright (e2e) |
| i18n | react-i18next / next-intl |

## 2.8 Frontendprestanda
| ID | Krav |
|---|---|
| FE-PF-001 | Code-splitting / lazy-loading av rutter. |
| FE-PF-002 | Mål-Web Vitals (LCP/CLS/INP) i grön zon. |
| FE-PF-003 | Effektiv rendering av det levande flödet (virtualisering vid stor volym). |

## 2.9 Testning
| ID | Krav |
|---|---|
| FE-QA-001 | Unit-tester av nyckelkomponenter och hooks. |
| FE-QA-002 | Integrationstester av formulär (auth, filter). |
| FE-QA-003 | E2E: registrering → koppling av Telegram → skapande av filter → mottagning av en matchning i flödet. |
| FE-QA-004 | Test av WebSocket-reconnect och felhantering. |
| FE-QA-005 | Kontroll i flera webbläsare och på mobil. |

## 2.10 Leveranser och acceptanskriterier
**Leveranser:**
1. Frontendens källkod i ett Git-repository.
2. Driftsatt webbapplikation, ansluten till backend från Etapp 1.
3. Instruktion för bygge/deploy/konfiguration av miljön.

**Acceptanskriterier:**
- Användaren går igenom hela vägen: registrering → koppling av Telegram → skapande av filter → levande flöde → historik.
- Det levande real-time-flödet uppdateras utan omladdning och överlever avbrott i anslutningen.
- Applikationen är responsiv (desktop + mobile) och lokaliserad (sv./eng.).
- Radering av konto/data (GDPR) är implementerad.

## 2.11 Etappens milstolpar
| Milstolpe | Innehåll |
|---|---|
| M5 — Skelett + Auth | Applikationens skelett, routing, registrering/inloggning mot API. |
| M6 — Filter + Telegram | CRUD för filter och koppling av Telegram. |
| M7 — Levande flöde + historik | WebSocket-flöde och aviseringshistorik. |
| M8 — Polering + deploy | UX/responsivitet/lokalisering/tester + produktionsdeploy. |

---

## Risker (frontend)
| Risk | Mitigering |
|---|---|
| Instabil WebSocket-anslutning | Auto-reconnect med backoff, fallback till polling, dedup på klienten. |
| Osynkat kontrakt med backend | Gemensamma typer/OpenAPI-klient, kontraktstester. |
| GDPR-avvikelse i UI | Skärm för radering av data, samtycken, länkar till policy. |
| Degradering vid stor flödesvolym | Virtualisering av listan, paginering. |

## Definition of Done (frontend)
- Acceptanskriterierna är uppfyllda; CI grön (lint + tester).
- E2E-scenariot går igenom stabilt.
- Responsivitet och lokalisering är kontrollerade på desktop och mobile.
- Applikationen är driftsatt och ansluten till produktions-API:t.

## Öppna frågor
1. Behövs en publik landningssida (SEO → Next.js) eller endast en skyddad dashboard (SPA)?
2. Planeras monetisering (abonnemang/fakturering)?
3. Behövs en adminpanel i denna etapp?
4. Vilka gränssnittsspråk är obligatoriska vid start (sv./eng./andra)?
