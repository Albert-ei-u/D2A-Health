from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


def _database_url() -> str:
    if settings.database_url.startswith("postgresql://"):
        return settings.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return settings.database_url


class Base(DeclarativeBase):
    pass


connect_args = {"check_same_thread": False} if _database_url().startswith("sqlite") else {}
engine = create_engine(_database_url(), connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    from app import db_models

    Base.metadata.create_all(bind=engine)
    if engine.dialect.name == "postgresql":
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE user_patient_records ADD COLUMN IF NOT EXISTS village VARCHAR(120)"))
            connection.execute(
                text(
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS "
                    "health_center VARCHAR(200) NOT NULL DEFAULT ''"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS "
                    "dataset_ready BOOLEAN NOT NULL DEFAULT FALSE"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS "
                    "email_verified BOOLEAN NOT NULL DEFAULT TRUE"
                )
            )
    elif "health_center" not in {
        column["name"] for column in inspect(engine).get_columns("users")
    }:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE users ADD COLUMN health_center VARCHAR(200) DEFAULT ''"))

    if "dataset_ready" not in {
        column["name"] for column in inspect(engine).get_columns("users")
    }:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE users ADD COLUMN dataset_ready BOOLEAN DEFAULT FALSE"))

    if "email_verified" not in {
        column["name"] for column in inspect(engine).get_columns("users")
    }:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT TRUE"))
