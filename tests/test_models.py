"""Enhetstester för pydantic-dokumentmodeller (Fas 1)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from shared.models import (
    Filter,
    Listing,
    ListingType,
    Notification,
    NotificationStatus,
    SeenListing,
    Source,
    User,
    UserStatus,
)


def test_user_valid_and_defaults():
    u = User(email="elin@hqrtm.se", password_hash="argon2$...")
    assert u.status == UserStatus.PENDING.value == "pending"
    assert u.locale == "sv"
    assert u.telegram_chat_id is None


def test_user_invalid_email():
    with pytest.raises(ValidationError):
        User(email="not-an-email", password_hash="x")


def test_filter_defaults():
    f = Filter(user_id="u1", name="Söder")
    assert f.only_fcfs is True
    assert f.is_active is True
    assert f.sources is None  # None → alla plattformar


def test_filter_rejects_negative_rent():
    with pytest.raises(ValidationError):
        Filter(user_id="u1", name="x", rent_min=-5)


def test_listing_source_aware():
    listing = Listing(
        source=Source.HOMEQ,
        external_id="abc123",
        title="2 rok Södermalm",
        url="https://homeq.se/listing/abc123",
        listing_type=ListingType.FCFS,
        rent=12500,
    )
    # use_enum_values=True → strängvärden lagras
    assert listing.source == "homeq"
    assert listing.listing_type == "fcfs"
    assert listing.external_id == "abc123"


def test_listing_requires_source():
    with pytest.raises(ValidationError):
        Listing(external_id="x", title="t", url="u")


def test_listing_default_type_unknown():
    listing = Listing(source=Source.QASA, external_id="q1", title="t", url="u")
    assert listing.listing_type == ListingType.UNKNOWN.value


def test_seen_and_notification_defaults():
    seen = SeenListing(source=Source.BLOCKET, external_id="b1")
    assert seen.source == "blocket"
    n = Notification(user_id="u1", listing_id="l1")
    assert n.status == NotificationStatus.QUEUED.value
    assert n.channel == "telegram"
