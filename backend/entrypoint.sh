#!/usr/bin/env sh
set -e

# Автоматически, без ручных шагов после `docker compose up`:
# 1) применяем миграции (создаёт таблицы и constraint пересечений),
# 2) запускаем сервер.
echo "Applying migrations..."
alembic upgrade head

echo "Seeding rooms and admin..."
python -m app.seed

echo "Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
