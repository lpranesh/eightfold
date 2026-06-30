"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings."""

    # Project
    PROJECT_NAME: str = "Candidate Data Transformer"
    VERSION: str = "1.0.0"

    # Flags
    ENABLE_NER: bool = False
    OCR_ENGINE: str = "tesseract"
    PDF_ENGINE: str = "pdfplumber"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
