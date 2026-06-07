# Установка и запуск

## Требования
- Python **3.12**
- MongoDB с **replica set** (рекомендуется **Atlas free-tier** — RS из коробки; нужно для Change Streams)

## Шаги
```bash
git clone https://github.com/alshfu/HQRTM.git
cd HQRTM

python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env        # заполнить MONGO_URI и секреты
pre-commit install

python -m shared.db                  # создать индексы MongoDB
flask --app web.app run --debug      # http://127.0.0.1:5000/
```

Открыть:
- `/` — лендинг, `/register` → `/app` — кабинет
- `/apidocs` — Swagger UI, `/health` — health-check

## MongoDB Atlas (быстрый старт)
1. Создать бесплатный кластер на cloud.mongodb.com.
2. Database Access — создать пользователя; Network Access — добавить свой IP.
3. Connect → Drivers → скопировать `mongodb+srv://…` в `MONGO_URI` в `.env`.

## Frontend (Tailwind)
Сейчас — Play CDN (ничего собирать не нужно). Production-сборка — см. `frontend-build/README.md`.

## Поллер и бот
`python -m poller.main` (Фаза 2) и `python -m bot.main` (Фаза 3) — появятся по мере реализации;
сейчас это заглушки. Поллер запускать только после фиксации ToS площадок (см. [Комплаенс](Compliance)).
