#!/bin/sh
set -e

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  alembic upgrade head
fi
if [ "${RUN_SEEDS:-0}" = "1" ]; then
  python app/seeds/seed_users.py
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
