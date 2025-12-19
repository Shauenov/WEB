# app/core/db.py
import time
from typing import Generator

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, create_engine, SQLModel

from app.core.config import settings

engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URL),
    pool_pre_ping=True,
    pool_size=getattr(settings, "DB_POOL_SIZE", 5),
    max_overflow=getattr(settings, "DB_MAX_OVERFLOW", 10),
    # echo=(settings.ENVIRONMENT == "local"),
)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

def _wait_for_db(retries: int = 30, delay: float = 1.0) -> None:
    """Wait for DB to accept connections."""
    for attempt in range(1, retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except OperationalError:
            if attempt == retries:
                raise
            time.sleep(delay)


def create_db_and_tables(drop_existing: bool = False, force: bool = False) -> None:
    """Create DB tables directly from SQLModel metadata without Alembic."""
    if settings.ENVIRONMENT != "local" and not force:
        raise RuntimeError("Table creation without migrations is limited to ENVIRONMENT=local (use force to override).")

    # Import models so they are registered on SQLModel.metadata before create_all
    import app.models  # noqa: F401

    _wait_for_db()
    if drop_existing:
        SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
