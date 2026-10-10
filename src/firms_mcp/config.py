"""Runtime configuration from environment variables (and an optional ``.env`` file).

Every variable is documented in ``.env.example`` and docs/developers/CONFIGURATION.md.
Secrets are held as ``SecretStr`` so they never appear in reprs or logs.
"""

from __future__ import annotations

from functools import lru_cache

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

    # Auth (ADR-0004) ---------------------------------------------------------------------
    allow_operator_key: bool = Field(
        default=False, validation_alias=AliasChoices("FIRMS_MCP_ALLOW_OPERATOR_KEY")
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
