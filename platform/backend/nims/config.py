from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve platform/.env when running from backend/ (e.g. `python -m nims` or `nims-api`).
_platform_dir = Path(__file__).resolve().parent.parent.parent
_backend_dir = Path(__file__).resolve().parent.parent
_ENV_FILES = (
    _platform_dir / ".env",
    _backend_dir / ".env",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[p for p in _ENV_FILES if p.is_file()] or None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://nims:nims_dev@localhost:5433/nims"
    jwt_secret: str = "dev-only-set-JWT_SECRET-in-production"
    jwt_expires_in: str = "12h"
    node_env: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
