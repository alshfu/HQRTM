# Справочник API

Интерактивная схема: **Swagger UI** на `/apidocs`, спецификация — `/openapi.json` (OpenAPI 3.0).
Авторизация: `Authorization: Bearer <access_token>` (JWT). Токены выдаёт `/auth/*`.

## Auth
| Метод | Путь | Тело | Ответ |
|---|---|---|---|
| POST | `/auth/register` | `{email, password}` | `201 {id, access_token, refresh_token}` · `400` слабый пароль/невалидно · `409` email занят |
| POST | `/auth/login` | `{email, password}` | `200 {id, access_token, refresh_token}` · `401` |
| POST | `/auth/refresh` | `{refresh_token}` | `200 {access_token}` · `401` |

## Фильтры (auth)
| Метод | Путь | Назначение |
|---|---|---|
| GET | `/api/filters` | список своих фильтров |
| POST | `/api/filters` | создать (тело — поля `Filter`, `user_id` игнорируется) |
| PUT | `/api/filters/<id>` | обновить |
| DELETE | `/api/filters/<id>` | удалить |

## Лента и уведомления (auth)
| Метод | Путь | Параметры |
|---|---|---|
| GET | `/api/listings` | `matched=true`, `source`, `listing_type`, `district`, `page`, `limit` (≤100) |
| GET | `/api/notifications` | `page`, `limit` |

## Telegram (auth)
| Метод | Путь | Ответ |
|---|---|---|
| POST | `/api/telegram/link` | `{link_code, deep_link}` |
| GET | `/api/telegram/status` | `{linked, bot_username}` |

## Профиль (auth)
| Метод | Путь | Назначение |
|---|---|---|
| GET | `/api/me` | профиль (`email`, `role`, `status`, `telegram_linked`) |
| DELETE | `/api/me` | удалить аккаунт и все данные (GDPR) |

## Прочее
| Метод | Путь | Назначение |
|---|---|---|
| GET | `/health` | health-check |
| GET | `/openapi.json`, `/apidocs` | OpenAPI + Swagger UI |

Пагинированные ответы: `{ items: [...], page, limit, total }`.
