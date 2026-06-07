# Модель данных (MongoDB)

Схемы — `shared/models.py` (pydantic), индексы — `shared/db.py` (`ensure_indexes`).
Уникальность объявления — составной ключ **(source, external_id)** (мульти-source агрегатор).

## Коллекции
| Коллекция | Ключевые поля | Индексы |
|---|---|---|
| `users` | email(unique), password_hash, **role**(user/admin), telegram_chat_id, link_code, status, locale, consent_at | `uniq_email` |
| `filters` | user_id, name, city, district, rent_min/max, rooms_min/max, area_min/max, only_fcfs, **sources**, is_active | `user_active(user_id,is_active)` |
| `listings` | **source**, external_id, title, url, district, rooms, area_m2, rent, listing_type, published_at, fetched_at | `uniq_source_extid(unique)`, `ttl_fetched(TTL)`, `match_type_district_rent` |
| `notifications` | user_id, listing_id, channel, status, latency_ms, error, sent_at | `user_sent(user_id,sent_at)` |
| `seen_listings` | source, external_id, seen_at | `uniq_seen(unique)`, `ttl_seen(TTL)` |
| `audit_log` | actor, action, payload, created_at | `created` |

## Перечисления
- `Source`: homeq, qasa, blocket, bostad_direkt, samtrygg, bostadsformedlingen, boplats
- `ListingType`: fcfs, queue, unknown
- `UserRole`: user, admin · `UserStatus`: pending, active, deleted
- `NotificationChannel`: telegram, email · `NotificationStatus`: queued, sent, delivered, failed

## Инварианты
- **DB-001 (уточнён):** уникум `(source, external_id)` — один external_id на разных площадках = разные объявления.
- **DB-002/003:** TTL `seen_listings.seen_at` (~24 ч), `listings.fetched_at` (~7 дн) — дедуп/очистка без Redis.
- **DB-004:** пароли — только хэш (Argon2).
- **DB-005:** `notifications.latency_ms` (publish→delivered) для SLA.
- **DB-006:** MongoDB как replica set (Change Streams) — Atlas из коробки.

Инициализация индексов: `python -m shared.db`.
