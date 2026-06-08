# Guide för gäst

**Gäst** — besökare utan inloggning. Vad som är tillgängligt:

## Utan registrering
- **Landningssida** (`/`) — tjänstebeskrivning, länkar till inloggning/registrering.
- **UI-demo** — https://alshfu.github.io/HQRTM/ — fullständigt panelgränssnitt med ett urval annonser
  från den riktiga parsern (desktop/tablet/mobil). Riktiga aviseringar och backend är inte anslutna.
  Testkonton för att se vyn som inloggad användare/admin:
  - användare: `elin@hqrtm.se` / `demo1234`
  - admin: `admin@hqrtm.se` / `admin1234`
- **API-dokumentation** (`/apidocs`, `/openapi.json`) — publikt REST API-schema.

## Inte tillgängligt
- Användarpanel (`/app/*`) — kräver inloggning; utan token omdirigeras klienten till `/login`.
- Skapa filter, koppla Telegram, träfflista.

## Bli användare
1. Öppna `/register`.
2. Ange e-post och lösenord (≥ 8 tecken), godkänn villkor/policy (GDPR).
3. Efter registrering loggas du in automatiskt och hamnar i panelen.

Vidare — [Guide för användare](User-Guide).
