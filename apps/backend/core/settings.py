"""
InsightIQ Backend — Core Settings

Pydantic-based configuration loaded from environment variables.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # ── App ──────────────────────────────────────────────────────
    app_name: str = Field(default="InsightIQ", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    secret_key: str = Field(default="dev-secret-change-me", alias="SECRET_KEY")

    # ── Server ───────────────────────────────────────────────────
    backend_host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        alias="CORS_ORIGINS",
    )

    # ── Supabase ─────────────────────────────────────────────────
    supabase_url: Optional[str] = Field(default=None, alias="SUPABASE_URL")
    supabase_anon_key: Optional[str] = Field(default=None, alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: Optional[str] = Field(
        default=None, alias="SUPABASE_SERVICE_ROLE_KEY"
    )
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")

    # ── Google Gemini ────────────────────────────────────────────
    google_api_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("GOOGLE_API_KEY", "GEMINI_API_KEY"),
        serialization_alias="GOOGLE_API_KEY"
    )
    gemini_model: str = Field(default="gemini-2.0-flash", alias="GEMINI_MODEL")

    # ── JWT ──────────────────────────────────────────────────────
    jwt_secret: Optional[str] = Field(default=None, alias="JWT_SECRET")

    # ── File Handling ────────────────────────────────────────────
    max_file_size_mb: int = Field(default=2048, alias="MAX_FILE_SIZE_MB")
    max_dataset_rows: int = Field(default=10_000_000, alias="MAX_DATASET_ROWS")
    upload_dir: str = Field(default="./uploads", alias="UPLOAD_DIR")

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def has_gemini(self) -> bool:
        return bool(self.google_api_key)

    @property
    def has_supabase(self) -> bool:
        return bool(self.supabase_url and self.supabase_anon_key)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
        "populate_by_name": True,
    }


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
