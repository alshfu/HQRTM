# API-referens

Interaktivt schema: **Swagger UI** på `/apidocs`, specifikation — `/openapi.json` (OpenAPI 3.0).

**Auktorisering — två sätt:**
- `Authorization: Bearer <access_token>` (JWT) — för API-klienter och webbläsartillägget.
- **httpOnly-cookies** (`hqrtm_access`/`hqrtm_refresh`) — sätts automatiskt av `/auth/*` och används av
  webbpanelen (token oåtkomlig för JS → XSS-skydd; `SameSite=Lax` → CSRF-skydd). Skickas automatiskt
  same-origin. Bearer-headern har företräde när båda finns.

## Auth
| Metod | Sökväg | Body | Svar |
|---|---|---|---|
| POST | `/auth/register` | `{email, password}` | `201 {id, access_token, refresh_token}` (+ Set-Cookie) · `400` svagt lösenord/ogiltigt · `409` e-post upptagen |
| POST | `/auth/login` | `{email, password}` | `200 {id, access_token, refresh_token}` (+ Set-Cookie) · `401` |
| POST | `/auth/refresh` | `{refresh_token}` *(eller refresh-cookie)* | `200 {access_token}` (+ Set-Cookie) · `401` |
| POST | `/auth/logout` | — | `200 {status}` — rensar auth-cookies |

## Filter (auth)
| Metod | Sökväg | Syfte |
|---|---|---|
| GET | `/api/filters` | lista egna filter |
| POST | `/api/filters` | skapa (body — `Filter`-fält, `user_id` ignoreras) |
| PUT | `/api/filters/<id>` | uppdatera |
| DELETE | `/api/filters/<id>` | radera |

## Flöde och aviseringar (auth)
| Metod | Sökväg | Parametrar |
|---|---|---|
| GET | `/api/listings` | `matched=true`, `source`, `listing_type`, `district`, `page`, `limit` (≤100) |
| GET | `/api/notifications` | `page`, `limit` |

## Telegram (auth)
| Metod | Sökväg | Svar |
|---|---|---|
| POST | `/api/telegram/link` | `{link_code, deep_link}` |
| GET | `/api/telegram/status` | `{linked, bot_username}` |

## Profil (auth)
| Metod | Sökväg | Syfte |
|---|---|---|
| GET | `/api/me` | profil (`email`, `role`, `status`, `locale`, `telegram_linked`) |
| DELETE | `/api/me` | radera konto och all data (GDPR) |

## Admin (roll `admin`)
Skydd `require_admin`: rollen kontrolleras mot databasen. Utan token — `401`, icke-admin — `403`.
| Metod | Sökväg | Syfte |
|---|---|---|
| GET | `/api/admin/stats` | räknare `{users, filters, listings, notifications}` |
| GET | `/api/admin/users` | användarlista (utan hemligheter), paginering |
| POST | `/api/admin/users/<id>/role` | byt roll `{role: "admin"\|"user"}`; kan inte degradera sig själv (`400`) |

## Realtid
| Metod | Sökväg | Syfte |
|---|---|---|
| GET | `/sse/feed?token=<access>` | SSE-ström av nya träffar (Change Stream på `notifications`) |

## Övrigt
| Metod | Sökväg | Syfte |
|---|---|---|
| GET | `/health` | health-check (liveness) |
| GET | `/health/ready` | readiness — pingar MongoDB (`200 ready` / `503 degraded`) |
| GET | `/openapi.json`, `/apidocs` | OpenAPI + Swagger UI |

Alla svar bär konservativa säkerhetsheaders (Fas 8): `X-Content-Type-Options`, `X-Frame-Options`,
`Referrer-Policy`, `Content-Security-Policy: frame-ancestors 'none'`, `Permissions-Policy`, samt
`Strict-Transport-Security` utanför testläge.

Paginerade svar: `{ items: [...], page, limit, total }`.

## i18n
Gränssnittsspråk: `?lang=sv\|en` (sparas i cookie `hqrtm_lang`, standard `sv`). Påverkar
serverrendering av mallar och inline-JS (katalogen skickas i `window.HQRTM_I18N`).
