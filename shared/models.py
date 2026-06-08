"""Pydantic-scheman för MongoDB-dokument (Roadmap §3, utökat för multi-källa).

Projektet är en aggregator: ett verktyg bevakar flera svenska bostadsplattformar.
Källan är isolerad i adaptern (`poller/sources/`), och här finns en enhetlig normaliserad
modell `Listing` med fältet `source`. Unikhet för annons — paret (source, external_id).

Kollektioner: users, filters, listings, notifications, seen_listings, audit_log.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


def _utcnow() -> datetime:
    return datetime.now(UTC)


# --------------------------------------------------------------------------- enums


class Source(StrEnum):
    """Källplattformar. Utökas i takt med att adaptrar läggs till (se poller/sources/)."""

    HOMEQ = "homeq"
    QASA = "qasa"
    BLOCKET = "blocket"
    BOSTAD_DIREKT = "bostad_direkt"
    SAMTRYGG = "samtrygg"
    BOSTADSFORMEDLINGEN = "bostadsformedlingen"
    BOPLATS = "boplats"


class ListingType(StrEnum):
    FCFS = "fcfs"  # «Först till kvarn» — måltyp
    QUEUE = "queue"  # kö / köpoäng — sållas bort av filtret only_fcfs
    UNKNOWN = "unknown"


class UserStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    DELETED = "deleted"


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class NotificationChannel(StrEnum):
    TELEGRAM = "telegram"
    EMAIL = "email"


class NotificationStatus(StrEnum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


# --------------------------------------------------------------------------- documents


class _Doc(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class User(_Doc):
    email: EmailStr
    password_hash: str
    role: UserRole = UserRole.USER
    telegram_chat_id: int | None = None
    link_code: str | None = None
    status: UserStatus = UserStatus.PENDING
    locale: str = "sv"
    consent_at: datetime | None = None  # GDPR: logg över samtycke
    created_at: datetime = Field(default_factory=_utcnow)


class Filter(_Doc):
    """Användarfilter. `sources=None` → alla plattformar; annars — endast de uppräknade."""

    user_id: str
    name: str
    city: str | None = None
    district: str | None = None
    rent_min: int | None = Field(default=None, ge=0)
    rent_max: int | None = Field(default=None, ge=0)
    rooms_min: float | None = Field(default=None, ge=0)
    rooms_max: float | None = Field(default=None, ge=0)
    area_min: float | None = Field(default=None, ge=0)
    area_max: float | None = Field(default=None, ge=0)
    only_fcfs: bool = True
    sources: list[Source] | None = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=_utcnow)


class Listing(_Doc):
    """Normaliserad annons från valfri plattform (BE-DE-006). Unikt: (source, external_id)."""

    source: Source
    external_id: str
    title: str
    url: str
    image_url: str | None = None  # bild på annonsen (källans primärbild) för flödet/vitrinen
    description: str | None = None  # kort beskrivning från källan
    address: str | None = None
    district: str | None = None
    rooms: float | None = None
    area_m2: float | None = None
    rent: int | None = Field(default=None, ge=0)
    listing_type: ListingType = ListingType.UNKNOWN
    published_at: datetime | None = None
    fetched_at: datetime = Field(default_factory=_utcnow)


class Notification(_Doc):
    user_id: str
    listing_id: str
    channel: NotificationChannel = NotificationChannel.TELEGRAM
    status: NotificationStatus = NotificationStatus.QUEUED
    latency_ms: int | None = None  # publish → delivered, för SLA (DB-005)
    error: str | None = None
    sent_at: datetime | None = None


class SeenListing(_Doc):
    """Dedup (BE-FL-003). Nyckel — (source, external_id), auto-rensning via TTL seen_at."""

    source: Source
    external_id: str
    seen_at: datetime = Field(default_factory=_utcnow)


class AuditLog(_Doc):
    actor: str
    action: str
    payload: dict | None = None
    created_at: datetime = Field(default_factory=_utcnow)
