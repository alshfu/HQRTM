"""OpenAPI 3.0-specifikation för API:t (BE-API-009).

Underhålls manuellt (utan tunga beroenden), serveras på `/openapi.json`;
Swagger UI — på `/apidocs` (CDN). Uppdatera vid tillägg/ändring av endpoints.
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
        "description": "API för bevakning av svenska uthyrningsplattformar (HomeQ, Qasa, …).",
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
                    "floor_min": {"type": "integer"},
                    "floor_max": {"type": "integer"},
                    "require_balcony": {"type": "boolean"},
                    "require_kitchen": {"type": "boolean"},
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
                "summary": "Registrering",
                "requestBody": {
                    "content": {
                        "application/json": {"schema": {"$ref": "#/components/schemas/Credentials"}}
                    }
                },
                "responses": {
                    "201": {"description": "skapad"},
                    "400": {"description": "ogiltigt/svagt lösenord"},
                    "409": {"description": "e-post upptagen"},
                },
            }
        },
        "/auth/login": {
            "post": {
                "summary": "Inloggning",
                "requestBody": {
                    "content": {
                        "application/json": {"schema": {"$ref": "#/components/schemas/Credentials"}}
                    }
                },
                "responses": {
                    "200": {
                        "description": "tokens",
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/Tokens"}}
                        },
                    },
                    "401": {"description": "felaktiga uppgifter"},
                },
            }
        },
        "/auth/refresh": {
            "post": {
                "summary": "Förnya access via refresh (body eller httpOnly-cookie)",
                "responses": {
                    "200": {"description": "access_token (+ Set-Cookie)"},
                    "401": {"description": "ogiltigt"},
                },
            }
        },
        "/auth/logout": {
            "post": {
                "summary": "Logga ut — rensa auth-cookies",
                "responses": {"200": {"description": "utloggad"}},
            }
        },
        "/api/filters": {
            "get": {
                "summary": "Lista filter",
                "security": _bearer,
                "responses": {"200": {"description": "items"}},
            },
            "post": {
                "summary": "Skapa filter",
                "security": _bearer,
                "requestBody": {
                    "content": {
                        "application/json": {"schema": {"$ref": "#/components/schemas/Filter"}}
                    }
                },
                "responses": {
                    "201": {"description": "skapad"},
                    "400": {"description": "ogiltigt"},
                },
            },
        },
        "/api/filters/{id}": {
            "put": {
                "summary": "Uppdatera filter",
                "security": _bearer,
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}
                ],
                "responses": {"200": {"description": "ok"}, "404": {"description": "saknas"}},
            },
            "delete": {
                "summary": "Ta bort filter",
                "security": _bearer,
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}
                ],
                "responses": {"200": {"description": "ok"}, "404": {"description": "saknas"}},
            },
        },
        "/api/listings": {
            "get": {
                "summary": "Flöde av annonser",
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
                "summary": "Aviseringshistorik",
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
                "summary": "Kopplingskod + deep-link",
                "security": _bearer,
                "responses": {"200": {"description": "link_code, deep_link"}},
            }
        },
        "/api/telegram/status": {
            "get": {
                "summary": "Status för Telegram-koppling",
                "security": _bearer,
                "responses": {"200": {"description": "linked, bot_username"}},
            }
        },
        "/sse/feed": {
            "get": {
                "summary": "SSE-flöde av träffar (real-time)",
                "description": "text/event-stream. Token i query `?token=`.",
                "parameters": [{"name": "token", "in": "query", "schema": {"type": "string"}}],
                "responses": {
                    "200": {"description": "händelseflöde"},
                    "401": {"description": "ogiltig token"},
                },
            }
        },
        "/api/me": {
            "get": {
                "summary": "Profil",
                "security": _bearer,
                "responses": {"200": {"description": "profil"}, "404": {"description": "saknas"}},
            },
            "delete": {
                "summary": "Ta bort konto och data (GDPR)",
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
