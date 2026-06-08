"""Central loggkonfiguration + PII-maskering (Fas 8, observerbarhet).

En enda konfigurationspunkt för loggar i web / poller / bot. Huvudkrav (§8 CLAUDE.md):
**loggar utan PII** — e-post, telegram_chat_id och tokens får inte läcka till loggarna.
`PiiRedactingFilter` rensar bort dem även om en utvecklare av misstag loggar ett objekt
med sådana fält.

Format — text som standard, JSON vid `LOG_JSON=true` (smidigt för aggregatorer i prod).
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from shared.config import get_settings

# e-post, "Bearer <token>", långa sifferföljder (chat_id/telefon) — maskeras.
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_BEARER_RE = re.compile(r"(Bearer\s+)[A-Za-z0-9._\-]+", re.IGNORECASE)
_LONGNUM_RE = re.compile(r"\b\d{7,}\b")  # telegram chat_id ~9–10 siffror, telefonnummer m.m.


def redact_pii(text: str) -> str:
    """Maskera e-post / Bearer-tokens / långa numeriska id:n i en sträng."""
    text = _EMAIL_RE.sub("[email]", text)
    text = _BEARER_RE.sub(r"\1[redacted]", text)
    text = _LONGNUM_RE.sub("[id]", text)
    return text


class PiiRedactingFilter(logging.Filter):
    """Filter som rensar PII ur det redan interpolerade loggmeddelandet."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:  # noqa: BLE001 — trasigt format får inte fälla loggningen
            return True
        record.msg = redact_pii(message)
        record.args = ()
        return True


class _JsonFormatter(logging.Formatter):
    """Minimal JSON-formatterare utan externa beroenden."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


_CONFIGURED = False


def setup_logging(level: str | None = None, json_fmt: bool | None = None) -> None:
    """Konfigurera rotloggern idempotent: format + PII-filter + nivå.

    Säker att anropa flera gånger (web-factory, tester) — hanteraren sätts en gång,
    upprepade anrop uppdaterar bara nivån.
    """
    global _CONFIGURED
    settings = get_settings()
    lvl = (level or settings.log_level).upper()
    use_json = settings.log_json if json_fmt is None else json_fmt

    root = logging.getLogger()
    root.setLevel(lvl)

    if _CONFIGURED:
        return

    handler = logging.StreamHandler()
    handler.addFilter(PiiRedactingFilter())
    if use_json:
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s", "%H:%M:%S")
        )
    root.addHandler(handler)
    _CONFIGURED = True
