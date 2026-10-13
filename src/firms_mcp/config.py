"""Runtime configuration from environment variables (and an optional ``.env`` file).

Every variable is documented in ``.env.example`` and docs/developers/CONFIGURATION.md.
Secrets are held as ``SecretStr`` so they never appear in reprs or logs.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

FIRMS_TRANSACTION_LIMIT = 5000  # per MAP_KEY per 10-minute interval (FIRMS map_key page)
FIRMS_TRANSACTION_WINDOW_SECONDS = 600


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    # FIRMS access ------------------------------------------------------------------------
    map_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("FIRMS_MAP_KEY"),
        description="FIRMS MAP_KEY for local (stdio) use; never logged",
    )
    firms_base_url: str = Field(
        default="https://firms.modaps.eosdis.nasa.gov",
        validation_alias=AliasChoices("FIRMS_API_BASE_URL"),
    )
    http_timeout_seconds: float = Field(
        default=60.0, gt=0, validation_alias=AliasChoices("FIRMS_MCP_HTTP_TIMEOUT")
    )
    http_retries: int = Field(default=2, ge=0, le=5, validation_alias="FIRMS_MCP_HTTP_RETRIES")
    retry_backoff_seconds: float = Field(
        default=0.5, ge=0, validation_alias=AliasChoices("FIRMS_MCP_RETRY_BACKOFF")
    )

    # Upstream discipline (ADR-0007) ------------------------------------------------------
    cache_ttl_nrt_seconds: int = Field(
        default=300, ge=0, validation_alias=AliasChoices("FIRMS_MCP_CACHE_TTL_NRT")
    )
    cache_ttl_sp_seconds: int = Field(
        default=21600, ge=0, validation_alias=AliasChoices("FIRMS_MCP_CACHE_TTL_SP")
    )
    cache_max_entries: int = Field(
        default=256, ge=0, validation_alias=AliasChoices("FIRMS_MCP_CACHE_MAX_ENTRIES")
    )
    transaction_budget: int = Field(
        default=4500,
        ge=1,
        le=FIRMS_TRANSACTION_LIMIT,
        validation_alias=AliasChoices("FIRMS_MCP_TRANSACTION_BUDGET"),
        description="Client-side ceiling per key per 10 minutes (FIRMS allows 5,000)",
    )

    # Links (ADR-0006) --------------------------------------------------------------------
    referral_params: bool = Field(default=True, validation_alias=AliasChoices("FIRMS_MCP_REFERRAL"))

    # Knowledge base (ADR-0005) ------------------------------------------------------------
    knowledge_dirs: str = Field(
        default="",
        validation_alias=AliasChoices("FIRMS_MCP_KNOWLEDGE_DIRS"),
        description="Extra knowledge directories, separated by os.pathsep (':' on Unix)",
    )

    # Server (ADR-0003) ---------------------------------------------------------------------
    host: str = Field(default="127.0.0.1", validation_alias=AliasChoices("FIRMS_MCP_HOST"))
    port: int = Field(default=8000, ge=1, le=65535, validation_alias=AliasChoices("FIRMS_MCP_PORT"))
    log_level: str = Field(default="INFO", validation_alias=AliasChoices("FIRMS_MCP_LOG_LEVEL"))

    # Auth (ADR-0004) ---------------------------------------------------------------------
    allow_operator_key: bool = Field(
        default=False, validation_alias=AliasChoices("FIRMS_MCP_ALLOW_OPERATOR_KEY")
    )
    auth_mode: Literal["oauth", "none"] = Field(
        default="oauth",
        validation_alias=AliasChoices("FIRMS_MCP_AUTH"),
        description="HTTP only: 'oauth' runs the MAP_KEY connect flow; 'none' disables it",
    )
    public_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("FIRMS_MCP_PUBLIC_URL"),
        description="Public base URL of the HTTP server (OAuth issuer and resource), e.g. https://firms-mcp.example.org",
    )
    token_keys: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("FIRMS_MCP_TOKEN_KEYS"),
        description="Token encryption keys, 'kid:base64url32bytes' comma-separated; first encrypts",
    )
    access_token_ttl_seconds: int = Field(
        default=3600, ge=60, le=86400, validation_alias=AliasChoices("FIRMS_MCP_ACCESS_TOKEN_TTL")
    )
    refresh_token_ttl_seconds: int = Field(
        default=30 * 24 * 3600,
        ge=3600,
        validation_alias=AliasChoices("FIRMS_MCP_REFRESH_TOKEN_TTL"),
    )
    enable_dcr: bool = Field(default=True, validation_alias=AliasChoices("FIRMS_MCP_ENABLE_DCR"))
    enable_cimd: bool = Field(default=True, validation_alias=AliasChoices("FIRMS_MCP_ENABLE_CIMD"))

    @property
    def effective_public_url(self) -> str:
        return (self.public_url or f"http://{self.host}:{self.port}").rstrip("/")

    @property
    def extra_knowledge_dirs(self) -> list[Path]:
        return [
            Path(part).expanduser()
            for part in self.knowledge_dirs.split(os.pathsep)
            if part.strip()
        ]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
