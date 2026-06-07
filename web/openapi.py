"""OpenAPI 3.0 спецификация API (BE-API-009).

Поддерживается вручную (без тяжёлых зависимостей), отдаётся на `/openapi.json`;
Swagger UI — на `/apidocs` (CDN). Обновлять при добавлении/изменении эндпоинтов.
"""

from __future__ import annotations

_bearer = [{"bearerAuth": []}]


def _paginated(item_ref: str) -> dict:
    return {
        "type": "object",
        "properties": {
            "items": {"type": "array", "items": {"$ref": item_ref}},
            "page": {"type": "integer"},
            "limit": {"type": "integer"},
            "total": {"type": "integer"},
        },
    }


OPENAPI_SPEC: dict = {
    "openapi": "3.0.3",
    "info": {
        "title": "HQRTM API",
        "version": "0.1.0",
        "description": "API агрегатора мониторинга шведских площадок аренды (HomeQ, Qasa, …).",
    },
    "components": {
        "securitySchemes": {
            "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
        },
        "schemas": {
            "Credentials": {
                "type": "object",
                "required": ["email", "password"],
                "properties": {
                    "email": {"type": "string", "format": "email"},
                    "password": {"type": "string", "minLength": 8},
                },
            },
            "Tokens": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "access_token": {"type": "string"},
                    "refresh_token": {"type": "string"},
                },
            },
            "Filter": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string"},
                    "city": {"type": "string"},
                    "district": {"type": "string"},
                    "rent_min": {"type": "integer"},
                    "rent_max": {"type": "integer"},
                    "rooms_min": {"type": "number"},
                    "rooms_max": {"type": "number"},
                    "area_min": {"type": "number"},
                    "area_max": {"type": "number"},
                    "only_fcfs": {"type": "boolean"},
                    "sources": {"type": "array", "items": {"type": "string"}},
                    "is_active": {"type": "boolean"},
                },
            },
            "Listing": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "source": {"type": "string"},
                    "external_id": {"type": "string"},
                    "title": {"type": "string"},
                    "url": {"type": "string"},
                    "district": {"type": "string"},
                    "rooms": {"type": "number"},
                    "area_m2": {"type": "number"},
                    "rent": {"type": "integer"},
                    "listing_type": {"type": "string"},
                },
            },
            "Notification": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "listing_id": {"type": "string"},
                    "channel": {"type": "string"},
                    "status": {"type": "string"},
                    "latency_ms": {"type": "integer"},
                },
            },
        },
    },
    "paths": {
        "/health": {
            "get": {"summary": "Health-check", "responses": {"200": {"description": "ok"}}}
        },
        "/auth/register": {
            "post": {
                "summary": "Регистрация",
                "requestBody": {
                    "content": {
                        "application/json": {"schema": {"$ref": "#/components/schemas/Credentials"}}
                    }
                },
                "responses": {
                    "201": {"description": "создан"},
                    "400": {"description": "невалидно/слабый пароль"},
                    "409": {"description": "email занят"},
                },
            }
        },
        "/auth/login": {
            "post": {
                "summary": "Вход",
                "requestBody": {
                    "content": {
                        "application/json": {"schema": {"$ref": "#/components/schemas/Credentials"}}
                    }
                },
                "responses": {
                    "200": {
                        "description": "токены",
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/Tokens"}}
                        },
                    },
                    "401": {"description": "неверные данные"},
                },
            }
        },
        "/auth/refresh": {
            "post": {
                "summary": "Обновить access по refresh",
                "responses": {
                    "200": {"description": "access_token"},
                    "401": {"description": "невалидно"},
                },
            }
        },
        "/api/filters": {
            "get": {
                "summary": "Список фильтров",
                "security": _bearer,
                "responses": {"200": {"description": "items"}},
            },
            "post": {
                "summary": "Создать фильтр",
                "security": _bearer,
                "requestBody": {
                    "content": {
                        "application/json": {"schema": {"$ref": "#/components/schemas/Filter"}}
                    }
                },
                "responses": {
                    "201": {"description": "создан"},
                    "400": {"description": "невалидно"},
                },
            },
        },
        "/api/filters/{id}": {
            "put": {
                "summary": "Обновить фильтр",
                "security": _bearer,
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}
                ],
                "responses": {"200": {"description": "ok"}, "404": {"description": "нет"}},
            },
            "delete": {
                "summary": "Удалить фильтр",
                "security": _bearer,
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}
                ],
                "responses": {"200": {"description": "ok"}, "404": {"description": "нет"}},
            },
        },
        "/api/listings": {
            "get": {
                "summary": "Лента объявлений",
                "security": _bearer,
                "parameters": [
                    {"name": "matched", "in": "query", "schema": {"type": "boolean"}},
                    {"name": "source", "in": "query", "schema": {"type": "string"}},
                    {"name": "page", "in": "query", "schema": {"type": "integer"}},
                    {"name": "limit", "in": "query", "schema": {"type": "integer"}},
                ],
                "responses": {
                    "200": {
                        "description": "items",
                        "content": {
                            "application/json": {
                                "schema": _paginated("#/components/schemas/Listing")
                            }
                        },
                    }
                },
            }
        },
        "/api/notifications": {
            "get": {
                "summary": "История уведомлений",
                "security": _bearer,
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer"}},
                    {"name": "limit", "in": "query", "schema": {"type": "integer"}},
                ],
                "responses": {
                    "200": {
                        "description": "items",
                        "content": {
                            "application/json": {
                                "schema": _paginated("#/components/schemas/Notification")
                            }
                        },
                    }
                },
            }
        },
        "/api/telegram/link": {
            "post": {
                "summary": "Код привязки + deep-link",
                "security": _bearer,
                "responses": {"200": {"description": "link_code, deep_link"}},
            }
        },
        "/api/telegram/status": {
            "get": {
                "summary": "Статус привязки Telegram",
                "security": _bearer,
                "responses": {"200": {"description": "linked, bot_username"}},
            }
        },
        "/api/me": {
            "get": {
                "summary": "Профиль",
                "security": _bearer,
                "responses": {"200": {"description": "профиль"}, "404": {"description": "нет"}},
            },
            "delete": {
                "summary": "Удалить аккаунт и данные (GDPR)",
                "security": _bearer,
                "responses": {"200": {"description": "ok"}},
            },
        },
    },
}


SWAGGER_UI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"><title>HQRTM API — Swagger UI</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    window.ui = SwaggerUIBundle({ url: "/openapi.json", dom_id: "#swagger-ui" });
  </script>
</body>
</html>"""
