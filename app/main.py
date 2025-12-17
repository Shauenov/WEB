# app/main.py
from contextlib import asynccontextmanager
from sqlalchemy import text
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.api.main import api_router
from app.core.db import engine
from app.core.config import settings
from app.utils.custom_docs import custom_swagger_ui_html


# ── lifespan: проверка подключения к БД ────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    yield


# ── FastAPI app ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Bus Project API",
    version="1.0.0",
    description="API docs",
    lifespan=lifespan,
    docs_url=None,   # выключаем стандартный Swagger UI
    redoc_url=None,
    openapi_url="/openapi.json",
)


# ── CORS ──────────────────────────────────────────────────────────────────────
if settings.ENVIRONMENT == "production":
    origins = ["https://juie.app"]
else:
    origins = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://juie.app",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Кастомная OpenAPI схема ───────────────────────────────────────────────────
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["openapi"] = "3.0.3" 
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    }

    for path in openapi_schema["paths"].values():
        for method in path.values():
            method.setdefault("security", [{"BearerAuth": []}])

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi


# ── Swagger UI с автологином ──────────────────────────────────────────────────
@app.get("/docs", include_in_schema=False)
async def overridden_swagger():
    return custom_swagger_ui_html(openapi_url="/openapi.json", title="Bus Project Docs")


# ── Healthcheck ───────────────────────────────────────────────────────────────
@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}


# ── API роутер ────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")
