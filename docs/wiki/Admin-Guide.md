# Guide för administratör

**Administratör** (roll `admin`) — sköter tjänsten: användare, källor, övervakning.

> Status: rollmodellen (`UserRole` = `user` | `admin`), admin-endpoints (`/api/admin/*`) och
> adminpanelen (`/app/admin`) är implementerade. Sidan beskriver både nuvarande funktioner och målbilden.

## Roller
- `user` — vanlig användare (standard vid registrering).
- `admin` — utökad åtkomst. Tilldelas **manuellt** (se nedan); ingen självregistrering till admin.

## Tilldela administratör
Via admin-endpoint (en admin byter roll i panelen) eller direkt i databasen:
```js
// mongosh, databasen hqrtm
db.users.updateOne({ email: "admin@hqrtm.se" }, { $set: { role: "admin" } })
```
Därefter visas menyvalet **Admin** i panelen.

## Administratörens funktioner
- **Användare**: lista, status, roll, Telegram-koppling, senaste aktivitet. Rollbyte
  (`/api/admin/users/<id>/role`) — man kan inte degradera sig själv.
- **Statistik**: `/api/admin/stats` — antal användare/filter/annonser/aviseringar.
- **Källor (mål)**: plattformsstatus (tillgänglig/otillgänglig), senaste parsningsfel, på/av för adapter.
- **Mätvärden (mål)**: latens publish→leverans (SLA ≤ 1,5 s), aviseringsvolym, bevakningsfrekvens.

## Övervakning (nuvarande)
- `GET /health` — webbprocessens status.
- `python -m shared.db` — (åter)skapa index i databasen.
- Processloggar (web/poller/bot) — strukturerade, utan PII.

## Säkerhet
- Åtkomst till andras data är blockerad på tjänstenivå (JWT-kontroll).
- Hemligheter — endast i `.env`/GitHub Secrets. Lösenord — Argon2. Mer: [Konfiguration](Configuration).

## Drift av källor
Aktivering av en plattformsadapter (`enabled=True` i `poller/sources/*`) är tillåten **endast** efter
positivt besked om plattformens ToS/robots.txt — se [Efterlevnad](Compliance).
