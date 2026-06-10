# Datamodell (MongoDB)

Scheman — `shared/models.py` (pydantic), index — `shared/db.py` (`ensure_indexes`).
Annonsens unikhet — sammansatt nyckel **(source, external_id)** (multi-source-aggregator).

## Kollektioner
| Kollektion | Nyckelfält | Index |
|---|---|---|
| `users` | email(unik), password_hash, **role**(user/admin), telegram_chat_id, link_code, status, locale, consent_at | `uniq_email` |
| `filters` | user_id, name, city, district, rent_min/max, rooms_min/max, area_min/max, **floor_min/max**, **require_balcony/require_kitchen**, only_fcfs, **sources**, is_active | `user_active(user_id,is_active)` |
| `listings` | **source**, external_id, title, url, image_url, description, district, rooms, area_m2, rent, **floor, has_balcony, has_kitchen**, listing_type, published_at, fetched_at | `uniq_source_extid(unik)`, `ttl_fetched(TTL)`, `match_type_district_rent` |
| `notifications` | user_id, listing_id, channel, status, latency_ms, error, sent_at | `user_sent(user_id,sent_at)` |
| `seen_listings` | source, external_id, seen_at | `uniq_seen(unik)`, `ttl_seen(TTL)` |
| `audit_log` | actor, action, payload, created_at | `created` |

## Uppräkningar
- `Source`: homeq, qasa, blocket, bostad_direkt, samtrygg, bostadsformedlingen, boplats
- `ListingType`: fcfs, queue, unknown
- `UserRole`: user, admin · `UserStatus`: pending, active, deleted
- `NotificationChannel`: telegram, email · `NotificationStatus`: queued, sent, delivered, failed

## Invarianter
- **DB-001 (preciserad):** unik `(source, external_id)` — samma external_id på olika plattformar = olika annonser.
- **DB-002/003:** TTL `seen_listings.seen_at` (~24 h), `listings.fetched_at` (~7 dgr) — dedup/städning utan Redis.
- **DB-004:** lösenord — endast hash (Argon2).
- **DB-005:** `notifications.latency_ms` (publish→delivered) för SLA.
- **DB-006:** MongoDB som replica set (Change Streams) — Atlas direkt.
- **Feature-extraktion:** `floor`/`has_balcony`/`has_kitchen` utvinns ur annonsens text
  (`poller/sources/base.py::extract_features`) eller källans strukturerade fält (Bostadsförmedlingen).
  `None` = okänt (sätts aldrig spekulativt False). Matchning: våning lenient, bekvämligheter strikta.

Initiera index: `python -m shared.db`.
