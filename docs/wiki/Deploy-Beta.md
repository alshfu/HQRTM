# Driftsättning — beta (web-only)

Beta-uppsättning enligt besluten: **web-only** (aviseringar i webbflödet via SSE, ingen Telegram än),
**PaaS** (Render som standard), data via **HomeQ:s publika Card Search**.

## Arkitektur

```
GitHub Actions cron (poll-homeq.yml, var 6:e min)
   └─ python -m poller.main --once  → publik HomeQ (Göteborg) → upsert listings
                                     → matcha filter → köa aviseringar
                                                │
                                          MongoDB Atlas (M0, replica set)
                                                │ Change Streams
   Render (Docker, gunicorn) ── web: API + Jinja2 + SSE ──► testarnas webbläsare
```

- **web** — Flask via `gunicorn` (gthread-workers för SSE). Render free.
- **poller** — körs som schemalagd cron (gratis via GitHub Actions) ELLER Render Cron/Worker (betalt).
- **db** — MongoDB Atlas **M0 (gratis)** är en replica set → Change Streams fungerar.

## Förutsättningar (ägaråtgärder)

- MongoDB Atlas-konto, Render-konto, detta repo.
- (Valfritt) egen domän — Render ger annars `*.onrender.com` med TLS.

## Steg

1. **MongoDB Atlas** — skapa ett gratis **M0**-kluster. Database Access: skapa användare.
   Network Access: tillåt `0.0.0.0/0` (eller Renders IP). Kopiera `mongodb+srv://…` → `MONGO_URI`.
2. **Render web** — New → **Blueprint** → välj repo (`render.yaml` upptäcks). Sätt hemligheten
   `MONGO_URI` i dashboarden. `SECRET_KEY`/`JWT_SECRET` genereras automatiskt. Deploy.
   Kontrollera `https://<app>.onrender.com/health` och `/health/ready` (DB-ping).
3. **Poller-cron** — lägg repo-hemligheten **`PROD_MONGO_URI`** (samma Atlas-sträng).
   `.github/workflows/poll-homeq.yml` kör då var 6:e minut: hämtar publik HomeQ (Göteborg),
   upsertar listings och köar aviseringar. (Första körningen skapar även index.)
4. **Verifiera** — registrera ett testkonto, skapa ett filter (t.ex. Göteborg, maxhyra), öppna
   flödet → matchande FCFS-annonser dyker upp i realtid (SSE).

## Hemligheter

| Var | Nyckel | Värde |
|---|---|---|
| Render web | `MONGO_URI` | Atlas-sträng |
| Render web | `SECRET_KEY`, `JWT_SECRET` | auto (`generateValue`) |
| Repo Secrets | `PROD_MONGO_URI` | Atlas-sträng (för poller-cron) |

## Återstår innan publika testare

- **Integritetspolicy + villkor** (GDPR) — idag platshållare; publicera riktig text (radering finns:
  `DELETE /api/me`).
- (Valfritt) **lösenordsåterställning / e-postverifiering** — finns ej än (register/login/refresh).

## Begränsningar & risker (beta)

- **Render free** sover efter ~15 min inaktivitet (första anropet väcker ~30 s). Bevakningen sköts
  ändå av poller-cron, oberoende av web-sömnen. Skala upp → betald plan (ingen sömn).
- **SSE** med flera gunicorn-workers: varje worker har en egen Change Stream-watcher (ok för beta).
- ⚠️ **ToS**: återkommande automatiserad åtkomst till HomeQ:s publika API (ägarens beslut/risk).
  Landlord-JWT/officiell 24/7-polling är fortsatt gated på ToS-bekräftelse (se [Efterlevnad](Compliance)).

## Skala upp senare

Render betald + **Background Worker** för pollern (alltid på, `python -m poller.main`); rate-limit på
**Redis** (`RATELIMIT_STORAGE_URI`); **httpOnly-cookie** för JWT (idag localStorage); **Telegram** (Fas 3).
