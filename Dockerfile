# HQRTM — gemensam image för web (gunicorn) och poller.
# Web (default):   gunicorn web.app:app
# Poller (cron):   docker run ... python -m poller.main --once
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

COPY pyproject.toml README.md ./
COPY shared ./shared
COPY web ./web
COPY poller ./poller
COPY bot ./bot
COPY scripts ./scripts

RUN pip install --upgrade pip && pip install -e .

EXPOSE 8000

# gthread-workers håller långlivade SSE-anslutningar utan att blockera (beta-skala).
# $PORT sätts av plattformen (Render m.fl.). Pollern startas via override-kommando.
CMD ["sh", "-c", "gunicorn -k gthread -w ${WEB_WORKERS:-2} --threads ${WEB_THREADS:-8} -b 0.0.0.0:${PORT:-8000} --timeout 120 web.app:app"]
