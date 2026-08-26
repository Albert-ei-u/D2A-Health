from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db import engine, init_db
from app.routers import ai, alerts, auth, dashboard, ingestion, insights, records

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def initialize_database() -> None:
    try:
        init_db()
    except SQLAlchemyError:
        # The API can still serve synthetic data when the database is temporarily unavailable.
        pass


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.get("/health/db")
def database_health_check() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "connected", "database": "postgresql"}
    except SQLAlchemyError:
        return {"status": "unavailable", "database": "postgresql"}


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(ingestion.router, prefix="/api/ingestion", tags=["ingestion"])
app.include_router(records.router, prefix="/api/records", tags=["records"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(insights.router, prefix="/api/insights", tags=["insights"])
