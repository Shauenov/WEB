# app/seeds/seed_users.py
import os, uuid, bcrypt
from datetime import datetime, timezone
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


ADMIN_PASS = os.getenv("ADMIN_PASS", "Admin#12345")
USER_PASS = os.getenv("USER_PASS", "User#12345")
SEED_ONCE = os.getenv("RUN_SEEDS_ONCE", "0") == "1"

ADMIN = {
    "id": str(uuid.uuid4()),
    "fullname": "Admin User",
    "phone": "+77410000001",
    "password": ADMIN_PASS,
    "role": "admin",
}
USER = {
    "id": str(uuid.uuid4()),
    "fullname": "Regular User",
    "phone": "+77410000002",
    "password": USER_PASS,
    "role": "user",
}


def hash_pw(p: str) -> str:
    return bcrypt.hashpw(p.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


UPSERT_SQL = text("""
    INSERT INTO users (id, fullname, phone, password, role, created_at, updated_at)
    VALUES (:id, :fullname, :phone, :password, :role, NOW(), NOW())
    ON CONFLICT (phone) DO UPDATE
    SET fullname   = EXCLUDED.fullname,
        password   = EXCLUDED.password,
        role       = EXCLUDED.role,
        updated_at = NOW()
""")


def upsert_user(conn, u: dict):
    params = {
        "id": u["id"],
        "fullname": u["fullname"],
        "phone": u["phone"],
        "password": hash_pw(u["password"]),
        "role": u["role"],
    }
    conn.execute(UPSERT_SQL, params)


def main():
    engine = create_engine(db_url(), future=True)
    with engine.begin() as conn:
        if SEED_ONCE:
            existing = conn.execute(text("SELECT 1 FROM users LIMIT 1")).first()
            if existing:
                print("Users already exist, skipping seeds.")
                return
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_users_phone ON users (phone)"))
        upsert_user(conn, ADMIN)
        upsert_user(conn, USER)
    print("Users seeded")


if __name__ == "__main__":
    main()
