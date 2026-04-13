# =====================================================================
# Dockerfile — Flight Analytics Platform
# Base image: Python 3.11 slim (lightweight, no GUI)
# =====================================================================
FROM python:3.11-slim

# Metadata
LABEL maintainer="mFadrhons"
LABEL project="COM_IATA Flight Analytics"

# ── System dependencies ───────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ─────────────────────────────────────────────────
WORKDIR /app

# ── Python dependencies ───────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy project source ───────────────────────────────────────────────
COPY . .

# ── Data directories (mounted at runtime via docker-compose volumes) ──
RUN mkdir -p /data/FORM /data/COM

# ── Default env ───────────────────────────────────────────────────────
ENV APP_ENV=cloud
ENV PYTHONUNBUFFERED=1

# Default command (overridden per service in docker-compose.yml)
CMD ["python", "main_page.py"]
