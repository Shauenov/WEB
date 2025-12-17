# app/core/db.py
from typing import Generator
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

def create_db_and_tables():
    if settings.ENVIRONMENT == "local":
        SQLModel.metadata.create_all(engine)
