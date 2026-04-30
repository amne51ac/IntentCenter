from functools import lru_cache
from pathlib import Path

from pydantic import Field
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
    # Optional. When set, used to derive the Fernet key for DB-stored IdP secrets; otherwise `jwt_secret` is used.
    identity_encryption_key: str | None = None
    # --- MCP: optional Streamable HTTP server for external LLM clients (same API tokens as REST). Off by default. ---
    mcp_enabled: bool = Field(default=False, validation_alias="NIMS_MCP_ENABLED")
    # --- Job execution: inline (synchronous in API) or async (PENDING; process with nims-worker). ---
    job_execution_mode: str = "inline"  # inline | async
    job_worker_poll_interval_sec: float = 2.0
    job_worker_batch_size: int = 5
    # --- Connector: at-rest secrets + outbound URL policy. ---
    # 44-byte urlsafe base64 Fernet key from `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
    # When unset, credentials are stored as raw JSON in DB (suitable for dev only).
    connector_secrets_fernet_key: str | None = None
    # During key rotation, decrypt with this, re-encrypt with primary; optional.
    connector_secrets_fernet_key_previous: str | None = None
    # Reference only (e.g. AWS KMS key ARN); wire a secrets backend before production. Not read by the app today.
    connector_secrets_kms_key_id: str | None = None
    # Block RFC1918, loopback, link-local, and metadata-style ranges before outbound requests.
    connector_url_block_private_networks: bool = True
    # If set, hostname must also match at least one suffix (e.g. "api.vendor.com,example.net"). Public IP URLs ignore this; use for corporate allowlists.
    connector_url_allowed_host_suffixes: str | None = None
    # Comma-separated, e.g. "https" or "https,http" for local dev. Production: https only.
    connector_url_http_allowed_schemes: str = "https,http"
    # Hardening: do not follow redirects to internal endpoints (recommend false).
    connector_http_follow_redirects: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
