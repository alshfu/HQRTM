#!/usr/bin/env python3
"""Generera tilläggets ikoner (16/32/48/128 px) utan externa beroenden.

Ritar HQRTM-märket: en grön rundad kvadrat (accent) med ett vitt hus.
Supersampling (4×) → mjuka kanter. PNG kodas för hand (zlib + CRC), ingen Pillow.

Kör: ``python extension/icons/gen_icons.py`` → skriver icon{16,32,48,128}.png i samma mapp.
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

ACCENT = (0x15, 0xB8, 0x78)  # HQRTM-grön
HOUSE = (0xFF, 0xFF, 0xFF)  # vitt hus
SS = 4  # supersampling


def _in_rounded_rect(x: float, y: float, r: float) -> bool:
    """Punkt (0..1, 0..1) inom rundad kvadrat med radie ``r``."""
    cx = min(max(x, r), 1 - r)
    cy = min(max(y, r), 1 - r)
    return (x - cx) ** 2 + (y - cy) ** 2 <= r * r


def _in_triangle(px, py, ax, ay, bx, by, cx, cy) -> bool:
    d1 = (px - bx) * (ay - by) - (ax - bx) * (py - by)
    d2 = (px - cx) * (by - cy) - (bx - cx) * (py - cy)
    d3 = (px - ax) * (cy - ay) - (cx - ax) * (py - ay)
    neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
    return not (neg and pos)


def _house(x: float, y: float) -> bool:
    """Vitt hus i normaliserade koordinater: tak (triangel) + kropp (rektangel)."""
    roof = _in_triangle(x, y, 0.50, 0.18, 0.16, 0.52, 0.84, 0.52)
    body = 0.27 <= x <= 0.73 and 0.50 <= y <= 0.82
    door = 0.44 <= x <= 0.56 and 0.62 <= y <= 0.82  # urklippt dörr → accentfärg
    return (roof or body) and not door


def _pixel(x: float, y: float) -> tuple[int, int, int, int]:
    """RGBA för en punkt i [0,1]². Transparenta hörn, accentbakgrund, vitt hus."""
    if not _in_rounded_rect(x, y, 0.22):
        return (0, 0, 0, 0)
    if _house(x, y):
        return (*HOUSE, 255)
    return (*ACCENT, 255)


def _render(size: int) -> bytes:
    """Rendera ``size``×``size`` RGBA-rader (supersamplade och nedskalade)."""
    big = size * SS
    rows = bytearray()
    for j in range(size):
        rows.append(0)  # PNG-filter "none" per rad
        for i in range(size):
            r = g = b = a = 0
            for sy in range(SS):
                for sx in range(SS):
                    px = (i * SS + sx + 0.5) / big
                    py = (j * SS + sy + 0.5) / big
                    cr, cg, cb, ca = _pixel(px, py)
                    r += cr
                    g += cg
                    b += cb
                    a += ca
            n = SS * SS
            rows += bytes((r // n, g // n, b // n, a // n))
    return bytes(rows)


def _png(size: int, raw: bytes) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)  # 8-bit RGBA
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def main() -> None:
    out = Path(__file__).parent
    for size in (16, 32, 48, 128):
        (out / f"icon{size}.png").write_bytes(_png(size, _render(size)))
        print(f"skrev icon{size}.png")


if __name__ == "__main__":
    main()
