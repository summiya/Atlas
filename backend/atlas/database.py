"""Database wiring: connection details live outside the API module.

For local Compose, host/user/name come from nonsecret configuration;
the password is loaded from a mounted file at runtime. No DSN or
password is embedded in the repository or passed via a URL env var.
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ATLAS_DB_", extra="ignore")
    host: str = "db"
    port: int = 5432
    name: str = "atlas"
    user: str = "atlas"
    password_file: str = "/run/secrets/atlas_db_password"


def connection_url(settings: DatabaseSettings) -> URL:
    """SQLAlchemy safely quotes credentials; don't log or stringify the URL."""
    password = Path(settings.password_file).read_text(encoding="utf-8").rstrip("\r\n")
    if not password:
        raise ValueError("Database password file is empty")
    return URL.create(
        drivername="postgresql+psycopg",
        username=settings.user,
        password=password,
        host=settings.host,
        port=settings.port,
        database=settings.name,
    )


@lru_cache(maxsize=1)
def get_engine():
    return create_engine(connection_url(DatabaseSettings()), pool_pre_ping=True)


@lru_cache(maxsize=1)
def get_session_factory():
    return sessionmaker(bind=get_engine(), expire_on_commit=False)
