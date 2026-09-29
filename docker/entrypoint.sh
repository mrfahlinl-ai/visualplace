#!/bin/sh
# Backend container entrypoint: apply migrations, then start the API.
set -e

echo "Running database migrations…"
alembic upgrade head

echo "Starting API…"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips="*"
