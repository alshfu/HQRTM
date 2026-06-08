# Konfiguration

Alla inställningar — via miljövariabler (`.env`, checkas inte in). Mall — `.env.example`.
Läses via `shared/config.py` (`pydantic-settings`).

| Variabel | Standard | Syfte |
|---|---|---|
| `MONGO_URI` | `mongodb://localhost:27017/?replicaSet=rs0` | Anslutning till MongoDB (Atlas: `mongodb+srv://…`) |
| `MONGO_DB` | `hqrtm` | Databasnamn |
| `SEEN_TTL_HOURS` | `24` | TTL för dedup (`seen_listings`) |
| `LISTINGS_TTL_DAYS` | `7` | TTL för auto-städning av `listings` |
| `FLASK_ENV` | `development` | Flask-läge |
| `SECRET_KEY` | `change-me-dev-only` | Flask-hemlighet (byt!) |
| `JWT_SECRET` | `change-me-dev-only` | JWT-hemlighet (byt! ≥ 32 byte) |
| `JWT_ACCESS_TTL_MIN` | `15` | TTL för access-token (min) |
| `JWT_REFRESH_TTL_DAYS` | `30` | TTL för refresh-token (dagar) |
| `TELEGRAM_BOT_TOKEN` | — | Bot-token (BotFather) |
| `TELEGRAM_BOT_USERNAME` | — | Botens username (för deep-link-koppling) |
| `POLL_INTERVAL_MS` | `3000` | Pollerns bevakningsintervall |
| `HOT_HOURS` | `08-22` | Fönster för «heta» timmar (adaptiv frekvens) |
| `HOMEQ_BASE_URL` | `https://api.homeq.se` | HomeQ Core API (demo: `https://api-demo.homeq.se`) |
| `HOMEQ_PUBLIC_BASE` | `https://homeq.se` | Bas för länkar till HomeQ-annonser |
| `HOMEQ_USERNAME` / `HOMEQ_PASSWORD` | — | HomeQ-integrationskonto (`/api/v2/tokens/`) |
| `HOMEQ_FETCH_AMOUNT` | `100` | Antal kort att hämta per pass |
| `QASA_API_URL` | `https://api.qasa.com/graphql` | Qasa GraphQL (kontrakt ej verifierat) |
| `QASA_PUBLIC_BASE` | `https://qasa.com` | Bas för länkar till Qasa-annonser |
| `QASA_FETCH_AMOUNT` | `50` | Antal Qasa-annonser per pass |
| `SAMTRYGG_API_URL` | — | Endpoint `GetHomePageObjects` (host saknas i specen — fastställ) |
| `SAMTRYGG_PUBLIC_BASE` | `https://samtrygg.se` | Bas för länkar till Samtrygg-annonser |
| `LOG_LEVEL` | `INFO` | Loggnivå |

> Adaptrarna HomeQ/Qasa/Samtrygg är som standard **avstängda** (`enabled=False` i koden) — aktivering
> först efter bekräftad ToS för plattformen (se [Efterlevnad](Compliance)). Ange uppgifter därefter.

## Generera hemligheter
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Säkerhet
- Publikt repo ⇒ **inga riktiga hemligheter** i kod/historik. Endast `.env` (i `.gitignore`) och
  GitHub Secrets. pre-commit `detect-secrets` skyddar mot läckor.
- I produktion måste `SECRET_KEY` och `JWT_SECRET` bytas till långa slumpvärden.
