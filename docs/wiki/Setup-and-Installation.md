# Installation och körning

## Krav
- Python **3.12**
- MongoDB med **replica set** (rekommenderas **Atlas free-tier** — RS direkt; krävs för Change Streams)

## Steg
```bash
git clone https://github.com/alshfu/HQRTM.git
cd HQRTM

python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env        # fyll i MONGO_URI och hemligheter
pre-commit install

python -m shared.db                  # skapa MongoDB-index
flask --app web.app run --debug      # http://127.0.0.1:5000/
```

Öppna:
- `/` — landningssida, `/register` → `/app` — panel
- `/apidocs` — Swagger UI, `/health` — health-check

## MongoDB Atlas (snabbstart)
1. Skapa ett gratis kluster på cloud.mongodb.com.
2. Database Access — skapa en användare; Network Access — lägg till din IP.
3. Connect → Drivers → kopiera `mongodb+srv://…` till `MONGO_URI` i `.env`.

## Frontend (Tailwind)
Production-bygget är incheckat (`web/static/css/app.css`) — inget behöver byggas för att köra.
Bygga om: se `frontend-build/README.md`.

## Poller och bot
`python -m poller.main` (Fas 2) och `python -m bot.main` (Fas 3, uppskjuten). Starta pollern först
efter fastställd ToS för plattformarna (se [Efterlevnad](Compliance)).
