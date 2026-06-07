# Contributing — HQRTM

## Рабочий процесс

1. Ветка от `develop`: `feature/<краткое-описание>` (или `fix/...`).
2. Изменения → коммиты → PR в `develop`. В `main` попадает только стабильное.
3. PR должен проходить CI: **ruff** (линт), **black** (формат), **pytest** (тесты).

## Перед коммитом

```bash
pip install -e ".[dev]"
pre-commit install        # один раз
ruff check . && black --check . && pytest
```

`pre-commit` запускает ruff/black и **detect-secrets** — последний защищает публичный
репозиторий от случайной утечки токенов/ключей. Если detect-secrets ругается на новый
«секрет», проверьте его и при необходимости обновите baseline:
`detect-secrets scan > .secrets.baseline`.

## Правила

- **Никаких секретов в коде/истории.** Только `.env` (в `.gitignore`) и GitHub Secrets.
- Соблюдайте прослеживаемость: в описании задачи/PR ссылайтесь на ID требования из ТЗ
  (`BE-DE-001`, `FE-FL-003` и т. п.).
- Стиль кода: ruff + black (настройки в `pyproject.toml`), строка ≤ 100.
- Логи — без PII (e-mail, telegram_chat_id и пр.).
- Парсер HomeQ изолирован в `poller/homeq_adapter.py` — при изменении источника правится только он.
