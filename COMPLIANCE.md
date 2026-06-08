# COMPLIANCE — HomeQ:s ToS, GDPR, etisk last

> ⚠️ **Utkast / TODO.** Dessa slutsatser måste fastställas **innan bevakningen startar (Fas 2)**.
> Så länge avsnitt är märkta TODO får riktig bevakning av HomeQ inte startas.

## 1. Källplattformar — ToS och robots.txt (per källa!)

Projektet är en **aggregator av flera svenska plattformar**. Var och en har egen ToS och `robots.txt` —
kontrolleras och fastställs **separat för varje**. En adapter aktiveras (`enabled=True`) först efter
positiv slutsats här. Adapterskelett: `poller/sources/`.

> ⚠️ Nedan är en **teknisk sammanfattning av research (2026-06-07), INTE juridisk rådgivning.** Innan
> någon adapter aktiveras: (1) läs plattformens aktuella ToS-text i sin helhet, (2) föredra officiellt API
> och skaffa nyckel/tillstånd, (3) vid skrapning — respektera robots.txt och rimlig last. Slutgiltigt
> beslut och ansvar ligger hos projektägaren.

| Plattform | `source` | robots.txt (nyckel) | Off. API | Rekommenderad väg | Adapter |
|---|---|---|---|---|---|
| HomeQ | `homeq` | `Disallow: /admin/`, sitemap finns | **JA** — Core API `docs-core.homeq.se` (REST, JWT, Card Search + webhooks) | Officiellt API (nyckel från landlord-portalen) — prioritet | ❌ tills nyckel |
| Qasa | `qasa` | öppen `/`; kontosidor och URL-filter förbjudna | Troligen samma API (Qasa Group, nycklar på `api.homeq.se`) | Officiellt API (fastställ) | ❌ |
| Blocket Bostad | `blocket` | hård anti-bot; inget API hittat | Inget publikt | Endast partnerskap; skrapning — hög risk (Schibsten ToS) | ❌ |
| Bostad Direkt | `bostad_direkt` | `Disallow: /RentalObject/Search`, `/NewSearch`, `/Home/Premium`, `/s` | Hittas ej | Respektera robots; ToS-kontroll; kontakta | ❌ |
| Samtrygg | `samtrygg` | öppen `/` | Möjligen (SwaggerHub `Samtryg/Samtrygg`) | Fastställ API-åtkomst; annars ToS | ❌ |
| Bostadsförmedlingen Sthlm | `bostadsformedlingen` | — | Partner-förmedling | Utanför prioritet (kö/köpoäng) | ❌ |
| Boplats | `boplats` | — | — | Utanför prioritet (kö) | ❌ |

> **I scope (ägarbeslut 2026-06-07):** HomeQ, Qasa, Blocket Bostad, Bostad Direkt, Samtrygg.
> Bostadsförmedlingen och Boplats — kandidater för senare (kö/köpoäng, inte FCFS-prioritet).

### Slutsatser och nästa steg
1. **HomeQ — prioritet nr 1: officiellt API finns** (`docs-core.homeq.se`, auth `/api/v2/tokens/`,
   Card Search av publicerade annonser, **webhooks** på händelser). Behövs: begär API-nyckel/partneråtkomst
   via landlord-portalen, fastställ villkoren för läsåtkomst för en consumer-tjänst.
   **Webhooks är idealiska för realtids-FCFS** (istället för högfrekvent bevakning).

   **Kontrakt avstämt 2026-06-07** (implementerat i `poller/sources/homeq.py`, adapter `enabled=False`):
   - Bas: prod `https://api.homeq.se`, demo `https://api-demo.homeq.se`. Nyckel från landlord-portalen
     (`homeq.se/biz` → settings/integration).
   - **Auth:** `POST /api/v2/tokens/` `{username, password}` → `{token: <JWT>, company, employee, ...}`;
     token i headern `Authorization: JWT <token>`; verifiering `POST /api/v2/tokens/verify/`.
   - **Card Search:** `POST /api/v3/cards/` → `{results: [...], total_hits}`. Kort: `id, type,
     title, uri, city/municipality/county, rent, rooms, area, location{lat,lon}, date_access, ...`.
     Flaggorna `first_come_first`/`queue_points` filtrerar typen på API-sidan → för FCFS efterfrågar vi
     `first_come_first=true, queue_points=false` (köbaserade kommer inte).
   - **Webhooks:** konfigureras i landlord-portalen, retries var 5:e min upp till 7 dagar; händelser
     agreement/reservation/signature/… är gjorda för landlord-flödet för signering, inte för publicering
     av annonser → för FCFS-bevakning passar Card Search bättre; webhooks — för framtiden.
   ⚠️ Detta är en teknisk avstämning mot dokumentationen, **inte** ett tillstånd att köra: aktivering av
   adaptern (`enabled=True`) — först efter erhållet konto och bekräftad ToS av ägaren.
2. **Qasa** — samma koncern; troligen samma API-åtkomst. Fastställ vid kontakt med HomeQ/Qasa.

   **Avstämningsstatus 2026-06-07:** något publikt dokumenterat partner-API för Qasa **hittades inte**
   (det finns en GraphQL-endpoint `api.qasa.com/graphql` som driver deras frontend, men utan officiell
   dokumentation för tredje part; ToS för programmatisk läsning ej bekräftad). Adaptern `poller/sources/qasa.py`
   är **implementerad mot ett best-effort GraphQL-schema `homes`** och märkt ⚠️ «kontrakt EJ verifierat»,
   `enabled=False`. **Före aktivering:** (1) bekräfta att åtkomsten är tillåten (partner-API HomeQ/Qasa
   eller skriftligt medgivande), (2) stäm av det verkliga GraphQL-schemat och justera `_HOMES_QUERY`/
   `_normalize`. Beslut om aktivering — ägarens.
3. **Blocket** — utan officiellt API + anti-bot + Schibsten ToS mot skrapning → **aktivera inte** utan
   partneravtal.
4. **Bostad Direkt** — robots.txt förbjuder söknings-endpoints → får inte bevakas; officiell kanal/
   ToS-kontroll krävs.
5. **Samtrygg** — kontrollera SwaggerHub-specen och villkoren för API-åtkomst.
6. **Ägaråtgärd:** kontakta HomeQ/Qasa om partner-API; för övriga — skriftligt tillstånd eller officiellt
   API innan adaptern aktiveras.

Källor: `docs-core.homeq.se`, `api.homeq.se/api-docs/`, plattformarnas robots.txt, SwaggerHub.

**Principer (enligt kravspec):**
- Officiellt API — prioritet. Skrapning — endast fallback och endast om det inte strider mot ToS.
- En **central** poller för alla användare (inte N personliga botar) — minskar lasten på källan.
- Rimliga intervall, jitter, exponentiell backoff, respekt för `429/503/Retry-After`, rotation av User-Agent.

## 2. GDPR (EU)

Vi lagrar personuppgifter: e-post, Telegram chat_id, användarens filter.

- [ ] **Rättslig grund** för behandling (användarens samtycke vid registrering).
- [ ] **Integritetspolicy** — text + länk i UI.
- [ ] **Rätt till radering** (right to erasure): `DELETE /api/me` raderar kontot och all relaterad data.
- [ ] **Samtyckeslogg** (`users.consent_at`).
- [ ] **Kryptering av hemligheter**, lösenord — endast hash (Argon2). Ingen PII i loggar.
- [ ] (Valfritt) Datahostingens geografi (EU-residens).

## 3. Utanför scope (begränsningar)

- Boten **loggar inte in** på användarens konto hos HomeQ.
- Boten **ansöker inte** om bostäder automatiskt.
- Tjänsten aviserar bara, med länk till annonsen.
