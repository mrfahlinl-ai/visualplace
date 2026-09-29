# VisualPlace backend (FastAPI). Multi-stage for a lean runtime image.
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps for Pillow / image handling + curl for the healthcheck.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libjpeg62-turbo zlib1g libwebp7 curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY backend/ ./
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Non-root runtime user; ensure the upload dir is writable.
RUN useradd -m -u 10001 appuser \
    && mkdir -p /app/var/uploads \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
