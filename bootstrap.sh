#!/usr/bin/env bash
set -euo pipefail

echo "Bootstrapping Ramblin Recs..."
cp -n backend/.env.example backend/.env || true

echo "Starting database..."
docker compose up -d db

echo "Waiting for DB health..."
for i in {1..30}; do
  if docker compose ps db | grep -q "(healthy)"; then
    echo "DB is healthy"
    break
  fi
  echo "Waiting..."; sleep 2
done

echo "Building API image and starting services..."
docker compose up -d --build api

echo "Running migrations..."
docker compose exec api alembic upgrade head

echo "Seeding data..."
docker compose exec api python scripts/seed.py --events 10000 --users 2000 --interactions 100000

echo "Starting placeholder web dev server..."
docker compose up -d web

echo "All set."
echo "API docs: http://localhost:8000/docs"
echo "Web dev server: http://localhost:5173"
