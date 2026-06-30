"""Application configuration using pydantic-settings.

All environment variables are validated at startup. Secrets are never hardcoded.
"""

from enum import Enum
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Deployment environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Supported log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All fields are validated via Pydantic. Sensitive values (database URL,
    secret key) must be provided through environment variables or a .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "Candidate Data Transformer"
    app_version: str = "1.0.0"
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    log_level: LogLevel = LogLevel.INFO

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000

    # --- Database ---
    database_url: str = Field(
        ...,
        description="PostgreSQL connection string",
        examples=["postgresql+asyncpg://user:pass@localhost:5432/candidate_db"],
    )
    database_pool_size: int = Field(default=10, ge=1, le=100)
    database_max_overflow: int = Field(default=20, ge=0, le=100)
    database_echo: bool = False

    # --- Security ---
    secret_key: str = Field(
        ...,
        min_length=32,
        description="Application secret key for signing",
    )
    cors_origins: list[str] = ["http://localhost:5173"]

    # --- Upload ---
    max_upload_size_mb: int = Field(default=50, ge=1, le=500)
    upload_dir: str = "/tmp/candidate_uploads"
    allowed_extensions: list[str] = [".pdf", ".csv", ".json", ".txt"]

    # --- Source Priorities (higher = more trusted) ---
    source_priority_resume: int = Field(default=90, ge=0, le=100)
    source_priority_linkedin: int = Field(default=85, ge=0, le=100)
    source_priority_github: int = Field(default=70, ge=0, le=100)
    source_priority_ats: int = Field(default=80, ge=0, le=100)
    source_priority_recruiter_csv: int = Field(default=60, ge=0, le=100)
    source_priority_recruiter_notes: int = Field(default=50, ge=0, le=100)

    # --- OCR ---
    tesseract_cmd: Optional[str] = None
    ocr_enabled: bool = True

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL uses a supported PostgreSQL driver."""
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError(
                "database_url must start with 'postgresql://' "
                "or 'postgresql+asyncpg://'"
            )
        return v

    @property
    def source_priorities(self) -> dict[str, int]:
        """Return source type to priority mapping."""
        return {
            "resume": self.source_priority_resume,
            "linkedin": self.source_priority_linkedin,
            "github": self.source_priority_github,
            "ats": self.source_priority_ats,
            "recruiter_csv": self.source_priority_recruiter_csv,
            "recruiter_notes": self.source_priority_recruiter_notes,
        }


def get_settings() -> Settings:
    """Factory function for Settings.

    Used as a FastAPI dependency so settings can be overridden in tests.
    """
    return Settings()
