"""Enhetstester för shared.utils (fönster för «heta» timmar)."""

from __future__ import annotations

import pytest
from shared.utils import is_hot_hour, parse_hot_hours


def test_parse_hot_hours_ok():
    assert parse_hot_hours("08-22") == (8, 22)
    assert parse_hot_hours("0-23") == (0, 23)


@pytest.mark.parametrize("bad", ["", "8", "8-25", "abc-10", "08:22"])
def test_parse_hot_hours_invalid(bad):
    with pytest.raises(ValueError):
        parse_hot_hours(bad)


def test_is_hot_hour_daytime_window():
    win = (8, 22)
    assert is_hot_hour(10, win) is True
    assert is_hot_hour(8, win) is True
    assert is_hot_hour(22, win) is False
    assert is_hot_hour(3, win) is False


def test_is_hot_hour_overnight_window():
    win = (22, 6)  # fönster över midnatt
    assert is_hot_hour(23, win) is True
    assert is_hot_hour(2, win) is True
    assert is_hot_hour(12, win) is False
