# Utvecklarguide

## Stack (kanon)
Flask 3 (API + Jinja2) · MongoDB (PyMongo + Motor) · separat asyncio-poller (`httpx`) ·
Telegram (`aiogram`) · realtid via MongoDB Change Streams + SSE · Tailwind + Vanilla JS.
Källa för stacken — `HQRTM_ToR_Flask_MongoDB_Roadmap.md`. Fullständig guide för AI-assistenter och
aktuell status — `CLAUDE.md` i roten.

## Struktur
```
shared/   config.py (pydantic-settings), db.py (klienter + ensure_indexes), models.py, security.py, utils.py
web/      app.py (factory), views.py (sidor), auth/ api/ admin/ sse/ (blueprints), templates/, static/js/api.js
poller/   main.py, detector.py, matcher.py, dispatcher.py, sources/ (multi-source-adaptrar)
bot/      main.py, handlers.py (aiogram)
tests/    pytest (mongomock + Flask test client)
frontend-build/  production-bygge av Tailwind → web/static/css/app.css
```

## Miljö
```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # fyll i MONGO_URI (Atlas) m.m.
pre-commit install
```

## Körning
```bash
python -m shared.db                  # MongoDB-index (en gång per databas)
flask --app web.app run --debug      # web: /, /app, /apidocs, /health
# python -m poller.main              # poller (Fas 2)
# python -m bot.main                 # bot (Fas 3, uppskjuten)
```

## Kvalitet och process
```bash
ruff check .        # lint
black .             # format
pytest -q           # tester
```
- Förgrening: `main` ← `develop` ← `feature/*`; ändringar via PR.
- **Huvudregel:** vid varje avslutad etapp — commit, push och uppdatera Wiki.
- pre-commit: ruff/black/detect-secrets (skydd mot hemlighetsläckor i publikt repo).
- CI (`.github/workflows/ci.yml`): ruff + black + pytest vid push/PR mot main|develop.
- Spårbarhet: referera till kravens ID i commits/PR (`BE-DE-001`, `FE-FL-003`, …).

## Konventioner
- Språk: **all kod och dokumentation skrivs på svenska** (kommentarer, docstrings, Wiki). Hemligheter —
  endast `.env`/Secrets, aldrig i kod/historik. Lösenord — Argon2. Loggar — utan PII.
- En plattforms parser är isolerad i sin adapter `poller/sources/<name>.py` (BE-DE-005).
- Annonsens unikhet — `(source, external_id)`. TTL-index istället för Redis.
- Stil: ruff + black, rad ≤ 100.

## Testning
- Unit: `shared.utils`, modeller, `detector`/`matcher`.
- Integration: API + index på `mongomock`, Flask test client (fixturer i `tests/conftest.py`:
  `db`, `client`, `make_user`, `bearer`).
