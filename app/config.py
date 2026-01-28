"""Application Configuration"""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Database
    DATABASE_URL: str
    TEST_DATABASE_URL: str | None = None

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Application
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["http://localhost:7654"]
    FRONTEND_URL: str = "http://localhost:7654"  # For generating invitation links
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False  # Set to False to disable SQL query logging


settings = Settings()
