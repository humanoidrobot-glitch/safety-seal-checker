#!/usr/bin/env bash
set -euo pipefail

echo "=== Running Alembic migrations ==="
alembic upgrade head

echo "=== Seeding database ==="
python scripts/seed_database.py

echo "=== Starting uvicorn on port ${PORT:-8000} ==="
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
