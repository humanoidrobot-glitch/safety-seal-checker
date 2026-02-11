#!/bin/bash
set -e

echo "==> Waiting for PostgreSQL to be ready..."
# Extract host and port from DATABASE_URL
# Format: postgresql://user:pass@host:port/dbname
DB_HOST=$(echo "$DATABASE_URL" | sed -n 's|.*@\([^:]*\):.*|\1|p')
DB_PORT=$(echo "$DATABASE_URL" | sed -n 's|.*:\([0-9]*\)/.*|\1|p')

until pg_isready -h "$DB_HOST" -p "$DB_PORT" > /dev/null 2>&1; do
    echo "    PostgreSQL is not ready yet — sleeping 2s..."
    sleep 2
done

echo "==> PostgreSQL is ready."

echo "==> Running Alembic migrations..."
alembic upgrade head

echo "==> Seeding database..."
python scripts/seed_database.py

echo "==> Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
