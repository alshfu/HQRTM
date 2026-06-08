# Efterlevnad (plattformarnas ToS, GDPR)

Fullständigt arbetsdokument med checklistor — `COMPLIANCE.md` i repots rot. Kortfattat:

## Plattformarnas ToS (per källa!)
Aggregatorn bevakar flera plattformar — var och en har **egen ToS och `robots.txt`**, kontrolleras
separat. En adapter (`poller/sources/*`) aktiveras (`enabled=True`) **endast** efter positivt besked.
I scope: HomeQ, Qasa, Blocket Bostad, Bostad Direkt, Samtrygg.

Principer: officiellt API först; skrapning — fallback och endast om det inte strider mot ToS;
en central poller; rimliga intervall + jitter + backoff; respekt för `429/503/Retry-After`.

**Research 2026-06-07 (kort, ej juridisk rådgivning):** **HomeQ har ett officiellt Core API**
(`docs-core.homeq.se`: JWT, Card Search av publicerade annonser, webhooks) — prioriterad väg;
Qasa — samma koncern (troligen samma API). Blocket — utan publikt API + anti-bot (endast partnerskap).
Bostad Direkt — robots.txt förbjuder söknings-endpoints. **Samtrygg** — har en publik SwaggerHub-spec
(`GetHomePageObjects`), **men host anges inte** och ToS för programmatisk läsning är inte bekräftad →
adaptern `enabled=False`, host (`SAMTRYGG_API_URL`) och ToS är ägarens beslut.
Fullständig tabell och steg — i `COMPLIANCE.md`.

## GDPR
- Rättslig grund — samtycke vid registrering (`users.consent_at`).
- Rätt till radering — `DELETE /api/me` raderar kontot och all relaterad data.
- Lösenord — Argon2; hemligheter — utanför repot; loggar — utan PII.
- Integritetspolicy och villkor — länkar i UI (platshållare tills texterna publiceras).

## Utanför scope
Boten **loggar inte in** på plattformskonton och **ansöker inte** — den aviserar bara.
