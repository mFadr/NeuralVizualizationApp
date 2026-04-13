FROM python:3.11-slim

LABEL maintainer="mFadrhons"
LABEL project="COM_IATA Flight Analytics"

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy project source ───────────────────────────────────────────────
COPY . .

# ── Copy data to persistent location ──────────────────────────────────
COPY data/ /data/

# ── Data directories (mounted at runtime via docker-compose volumes) ──
RUN mkdir -p /data/FORM /data/COM

# ── Default env ───────────────────────────────────────────────────────
ENV APP_ENV=cloud
ENV PYTHONUNBUFFERED=1

# Default command (overridden per service in docker-compose.yml)
CMD ["python", "main_page.py"]