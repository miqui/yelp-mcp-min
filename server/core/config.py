"""
Application configuration via pydantic-settings.

Priority (highest → lowest):
  1. Environment variables
  2. .env file
  3. Field defaults

Required:
  YELP_API_KEY — Yelp Fusion API v3 bearer token.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Resolved configuration for the Yelp MCP server."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    yelp_api_key: str = Field(..., description="Yelp Fusion API bearer token")
    yelp_base_url: str = Field(
        default="https://api.yelp.com/v3",
        description="Yelp Fusion API base URL",
    )

    # HTTP client tunables
    http_timeout: float = Field(default=10.0, ge=1.0, le=60.0)
    http_max_retries: int = Field(default=3, ge=0, le=5)
    http_retry_wait_min: float = Field(default=1.0, ge=0.1)
    http_retry_wait_max: float = Field(default=10.0, ge=1.0)

    log_level: str = Field(default="INFO")
    json_logs: bool = Field(default=False)


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the cached Settings singleton, constructing it on first call."""
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore[call-arg]
    return _settings
