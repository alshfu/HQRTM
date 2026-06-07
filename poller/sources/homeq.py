"""Адаптер HomeQ (homeq.se) — первый источник, FCFS «Först till kvarn».

Путь реализации (ресёрч 2026-06-07, см. COMPLIANCE.md): **официальный HomeQ Core API**
(`docs-core.homeq.se`, база `api.homeq.se`). Контракт:

* **Auth:** ``POST /api/v2/tokens/`` с ``{"username", "password"}`` → ``{"token": <JWT>, ...}``.
  Токен передаётся в заголовке ``Authorization: JWT <token>``; на 401 — перелогин.
* **Card Search:** ``POST /api/v3/cards/`` → ``{"results": [...], "total_hits": N}``.
  Флаги ``first_come_first``/``queue_points`` фильтруют тип карточки на стороне API:
  для FCFS-мониторинга запрашиваем ``first_come_first=True, queue_points=False`` —
  очередные объявления вообще не приходят, отсев на источнике (BE-FL-002).
  Сортировка ``publish_date.desc`` → самые свежие сверху.

Ключ/доступ — из landlord-портала (``homeq.se/biz`` → settings/integration). Нужны учётные
данные интеграции в ``.env`` (``HOMEQ_USERNAME``/``HOMEQ_PASSWORD``).

⚠️ ``enabled=False`` до подтверждения ToS и получения доступа (COMPLIANCE.md) — поллер
адаптер не опрашивает. Включение (``enabled=True``) — решение владельца проекта.

При изменении контракта/разметки источника правится ТОЛЬКО этот файл (BE-DE-005).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from shared.config import get_settings
from shared.models import ListingType, Source

from poller.sources.base import SourceAdapter, as_float, as_int
from poller.sources.registry import register

log = logging.getLogger("hqrtm.poller.homeq")

_AUTH_PATH = "/api/v2/tokens/"
_CARDS_PATH = "/api/v3/cards/"


class HomeQAuthError(RuntimeError):
    """Не удалось получить/обновить JWT (нет учётки или отказ API)."""


@register
class HomeQAdapter(SourceAdapter):
    source = Source.HOMEQ
    enabled = False  # включить после проверки ToS (COMPLIANCE.md) — решение владельца

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        """``client`` можно внедрить (тесты/общий пул); иначе создаётся по запросу."""
        self._client = client
        self._owns_client = client is None
        self._token: str | None = None

    # ---------------------------------------------------------------- lifecycle

    def _build_client(self) -> httpx.AsyncClient:
        s = get_settings()
        return httpx.AsyncClient(
            base_url=s.homeq_base_url,
            timeout=s.homeq_timeout_s,
            headers={"Content-Type": "application/json"},
        )

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = self._build_client()
        return self._client

    async def aclose(self) -> None:
        """Закрыть внутренний клиент (если создавали сами)."""
        if self._client is not None and self._owns_client:
            await self._client.aclose()
            self._client = None

    # ---------------------------------------------------------------- auth

    async def _authenticate(self, client: httpx.AsyncClient) -> str:
        s = get_settings()
        if not s.homeq_username or not s.homeq_password:
            raise HomeQAuthError("HOMEQ_USERNAME/HOMEQ_PASSWORD не заданы (.env)")
        resp = await client.post(
            _AUTH_PATH,
            json={"username": s.homeq_username, "password": s.homeq_password},
        )
        if resp.status_code != 200:
            raise HomeQAuthError(f"auth {resp.status_code}: {resp.text[:200]}")
        token = resp.json().get("token")
        if not token:
            raise HomeQAuthError("в ответе auth нет поля token")
        self._token = token
        return token

    async def _token_or_auth(self, client: httpx.AsyncClient) -> str:
        return self._token or await self._authenticate(client)

    # ---------------------------------------------------------------- fetch

    async def fetch_listings(self) -> list[dict]:
        """Вернуть свежие FCFS-карточки HomeQ, нормализованные в поля ``Listing``."""
        client = await self._get_client()
        token = await self._token_or_auth(client)

        body = {
            "offset": 0,
            "amount": get_settings().homeq_fetch_amount,
            "sorting": "publish_date.desc",
            "first_come_first": True,  # только «först till kvarn»
            "queue_points": False,  # очередные отсекаем на источнике
        }
        resp = await self._cards(client, token, body)

        # JWT мог протухнуть — один перелогин и повтор.
        if resp.status_code == 401:
            token = await self._authenticate(client)
            resp = await self._cards(client, token, body)

        if resp.status_code == 429 or resp.status_code >= 500:
            # Транзиентный сбой/троттлинг — пробрасываем, цикл сделает backoff (BE-RS-002).
            retry_after = resp.headers.get("Retry-After")
            raise httpx.HTTPStatusError(
                f"HomeQ cards {resp.status_code}"
                + (f" Retry-After={retry_after}" if retry_after else ""),
                request=resp.request,
                response=resp,
            )
        resp.raise_for_status()

        results = resp.json().get("results", [])
        return [self._normalize(card) for card in results if card.get("id") is not None]

    async def _cards(self, client: httpx.AsyncClient, token: str, body: dict) -> httpx.Response:
        return await client.post(_CARDS_PATH, json=body, headers={"Authorization": f"JWT {token}"})

    # ---------------------------------------------------------------- normalize

    def _normalize(self, card: dict[str, Any]) -> dict:
        """Карточка HomeQ → dict с полями модели ``Listing`` (+ ``fcfs`` для детектора)."""
        ext_id = str(card["id"])
        return {
            "source": str(self.source),
            "external_id": ext_id,
            "title": card.get("title") or "Bostad",
            "url": self._listing_url(card, ext_id),
            "district": card.get("municipality") or card.get("city"),
            "rooms": as_float(card.get("rooms")),
            "area_m2": as_float(card.get("area")),
            "rent": as_int(card.get("rent")),
            # Запрос с first_come_first=True/queue_points=False → пришли только FCFS.
            "listing_type": ListingType.FCFS.value,
            "fcfs": True,
        }

    def _listing_url(self, card: dict, ext_id: str) -> str:
        uri = card.get("uri")
        base = get_settings().homeq_public_base.rstrip("/")
        if uri:
            if uri.startswith(("http://", "https://")):
                return uri
            return f"{base}/{str(uri).lstrip('/')}"
        return f"{base}/listing/{ext_id}"
