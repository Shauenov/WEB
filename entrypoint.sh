#!/bin/sh
set -e

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  if python - <<'PY'
import os
from sqlalchemy import create_engine, text

def db_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    u = os.getenv("POSTGRES_USER")
    p = os.getenv("POSTGRES_PASSWORD")
    d = os.getenv("POSTGRES_DB")
    h = os.getenv("POSTGRES_HOST", "bus-db")
    port = os.getenv("POSTGRES_PORT", "5432")
    if not (u and p and d):
        raise SystemExit("DATABASE_URL is not set and POSTGRES_* are missing")
    return f"postgresql+psycopg2://{u}:{p}@{h}:{port}/{d}"

engine = create_engine(db_url(), future=True)
with engine.connect() as conn:
    has_alembic = conn.execute(text("SELECT to_regclass('alembic_version')")).scalar() is not None
    has_tables = conn.execute(
        text("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname='public' AND tablename!='alembic_version')")
    ).scalar()

if has_tables and not has_alembic:
    raise SystemExit(0)
raise SystemExit(1)
PY
  then
    alembic stamp head
  else
    alembic upgrade head
  fi
fi
if [ "${RUN_SEEDS:-0}" = "1" ]; then
  python app/seeds/seed_users.py
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
