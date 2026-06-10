# Contributing — HQRTM

## Arbetsflöde

1. Gren från `develop`: `feature/<kort-beskrivning>` (eller `fix/...`).
2. Ändringar → commits → PR mot `develop`. Endast stabilt går till `main`.
3. **Huvudregel:** vid varje avslutad etapp — commit, push och uppdatera Wiki (`docs/wiki/`).
4. PR måste klara CI: **ruff** (lint), **black** (format), **pytest** (tester).

## Före commit

```bash
pip install -e ".[dev]"
pre-commit install        # en gång
ruff check . && black --check . && pytest
```

`pre-commit` kör ruff/black och **detect-secrets** — det sista skyddar det publika repot mot
oavsiktligt läckta tokens/nycklar. Om detect-secrets klagar på en ny «hemlighet», kontrollera den
och uppdatera vid behov baseline: `detect-secrets scan > .secrets.baseline`.

## Regler

- **Språk: all kod och dokumentation skrivs på svenska** (kommentarer, docstrings, Wiki).
  Kommunikationen i ärenden/PR kan vara på projektets vanliga språk.
- **Inga hemligheter i kod/historik.** Endast `.env` (i `.gitignore`) och GitHub Secrets.
- Spårbarhet: referera till kravens ID i ärende/PR (`BE-DE-001`, `FE-FL-003` o.s.v.).
- Kodstil: ruff + black (inställningar i `pyproject.toml`), rad ≤ 100.
- Loggar — utan PII (e-post, telegram_chat_id m.m.).
- En plattforms parser är isolerad i sin adapter `poller/sources/<name>.py` — vid källändring
  rättas endast den filen (BE-DE-005).

## Bidragsgivare

- Alexander Shchetinin — skapare och underhållare
- Pushkinho (Petros) — <Petros@maktic.se>
