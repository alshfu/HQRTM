# Гид разработчика

## Стек (канон)
Flask 3 (API + Jinja2) · MongoDB (PyMongo + Motor) · отдельный asyncio-поллер (`httpx`) ·
Telegram (`aiogram`) · real-time через MongoDB Change Streams + SSE · Tailwind + Vanilla JS.
Источник истины по стеку — `HQRTM_ToR_Flask_MongoDB_Roadmap.md`. Полное руководство для ИИ-ассистентов
и текущий статус — `CLAUDE.md` в корне.

## Структура
```
shared/   config.py (pydantic-settings), db.py (клиенты + ensure_indexes), models.py, security.py, utils.py
web/      app.py (фабрика), views.py (страницы), auth/ api/ (blueprints), templates/, static/js/api.js
poller/   main.py, detector.py, matcher.py, dispatcher.py, sources/ (мульти-source адаптеры)
bot/      main.py, handlers.py (aiogram)
tests/    pytest (mongomock + Flask test client)
frontend-build/  production-сборка Tailwind (сейчас — Play CDN)
```

## Окружение
```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # заполнить MONGO_URI (Atlas) и пр.
pre-commit install
```

## Запуск
```bash
python -m shared.db                  # индексы MongoDB (один раз на БД)
flask --app web.app run --debug      # web: /, /app, /apidocs, /health
# python -m poller.main              # поллер (Фаза 2)
# python -m bot.main                 # бот (Фаза 3)
```

## Качество и процесс
```bash
ruff check .        # линт
black .             # формат
pytest -q           # тесты
```
- Ветвление: `main` ← `develop` ← `feature/*`; изменения через PR в `develop`.
- pre-commit: ruff/black/detect-secrets (анти-утечка секретов в public repo).
- CI (`.github/workflows/ci.yml`): ruff + black + pytest на push/PR в main|develop.
  ⚠️ Если Actions не запускаются — проверьте биллинг аккаунта GitHub (блокировка отключает Actions).
- Прослеживаемость: в коммитах/PR ссылайтесь на ID требований (`BE-DE-001`, `FE-FL-003`, …).

## Соглашения
- Секреты — только `.env`/Secrets, никогда в коде/истории. Пароли — Argon2. Логи — без PII.
- Парсер площадки изолирован в своём адаптере `poller/sources/<name>.py` (BE-DE-005).
- Уникум объявления — `(source, external_id)`. TTL-индексы вместо Redis.
- Стиль: ruff + black, строка ≤ 100.

## Тестирование
- Unit: `shared.utils`, модели, (далее `detector`/`matcher`).
- Integration: API + индексы на `mongomock`, Flask test client (фикстуры в `tests/conftest.py`:
  `db`, `client`, `make_user`, `bearer`).
