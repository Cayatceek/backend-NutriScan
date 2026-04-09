from __future__ import annotations

import json
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="NUTRISCAN_",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "NutriScan API"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./nutriscan.db"
    allowed_origins: list[str] = ["*"]
    jwt_secret: str = "change-me-for-production"
    jwt_issuer: str = "nutriscan-backend"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30
    refresh_token_pepper: str = "change-me-refresh-pepper"
    password_reset_token_pepper: str = "change-me-reset-pepper"
    internal_api_key: str = "dev-internal-api-key"
    open_food_facts_base_url: str = "https://world.openfoodfacts.org"
    open_food_facts_user_agent: str = "NutriScan/1.0 (Android)"
    request_timeout_seconds: int = 30
    password_reset_token_ttl_minutes: int = 30
    debug_password_reset_tokens: bool = False
    auth_rate_limit_count: int = 10
    auth_rate_limit_window_seconds: int = 60
    off_rate_limit_count: int = 60
    off_rate_limit_window_seconds: int = 60

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: object) -> object:
        if not isinstance(value, str):
            return value

        stripped = value.strip()
        if not stripped:
            return []

        if stripped.startswith("["):
            return json.loads(stripped)

        return [item.strip() for item in stripped.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
