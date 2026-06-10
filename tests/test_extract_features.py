"""Tester för feature-extraktion ur annonstext (balkong/kök/våning).

Källornas list-API:er saknar dessa fält → vi utvinner dem ur annonsens egen text
(riktig källdata, ingen fiktion). Hittas inget → nyckeln utelämnas (okänt).
"""

from __future__ import annotations

from poller.sources.base import extract_features


def test_balcony_detected():
    assert extract_features("Ljus 2:a med stor balkong")["has_balcony"] is True
    assert extract_features("Trevlig lägenhet, egen uteplats")["has_balcony"] is True


def test_kitchen_detected():
    assert extract_features("Renoverat kök och badrum")["has_kitchen"] is True
    assert extract_features("Liten etta med kokvrå")["has_kitchen"] is True


def test_floor_variants():
    assert extract_features("3:e våningen, hiss finns")["floor"] == 3
    assert extract_features("Lägenhet på vån 5")["floor"] == 5
    assert extract_features("Mysig 2:a, 4 tr")["floor"] == 4
    assert extract_features("Plan 7 med utsikt")["floor"] == 7
    assert extract_features("Bottenvåning med trädgård")["floor"] == 0


def test_nothing_found_returns_empty():
    assert extract_features("Ljus lägenhet nära centrum") == {}
    assert extract_features(None, "") == {}


def test_only_positive_findings():
    # ingen spekulativ False/0 när inget nämns
    out = extract_features("2 rum och kök med balkong, vån 2")
    assert out == {"has_balcony": True, "has_kitchen": True, "floor": 2}


def test_floor_sanity_bound():
    # orimligt högt tal tolkas inte som våning
    assert "floor" not in extract_features("hyra 9999 tr för dyrt")
