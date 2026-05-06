from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Gym App API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Environment
    ENVIRONMENT: Literal["development", "production"] = "development"

    # CORS (comma-separated; env var overrides default)
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://app.costabirra.com",
    ]

    # Database - can be set directly via DATABASE_URL env var, or falls back to environment-based defaults
    DATABASE_URL: str = "sqlite+aiosqlite:///./gym_app.db"

    @property
    def DATABASE_CONNECT_ARGS(self) -> dict:
        """Returns connection arguments specific to the database type"""
        # Auto-detect database type from the URL
        if "sqlite" in self.DATABASE_URL.lower():
            return {"check_same_thread": False}
        return {}

    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Email Configuration
    EMAIL_USE_MOCK: bool = True  # Set to False for production SMTP
    EMAIL_FROM: str = "noreply@gymapp.com"
    EMAIL_SMTP_HOST: str = "localhost"
    EMAIL_SMTP_PORT: int = 587
    EMAIL_SMTP_USER: str = ""
    EMAIL_SMTP_PASSWORD: str = ""
    EMAIL_SMTP_TLS: bool = True
    FRONTEND_URL: str = "http://localhost:5173"

    # Program Builder
    # Local dev: ENGINE_INVOCATION_MODE=http, ENGINE_URL=http://localhost:8000
    # Production: ENGINE_INVOCATION_MODE=lambda, ENGINE_LAMBDA_FUNCTION_NAME=<fn-name>
    ENGINE_INVOCATION_MODE: Literal["http", "lambda"] = "http"
    ENGINE_URL: str = "http://localhost:8000"
    ENGINE_LAMBDA_FUNCTION_NAME: str = "program-builder"
    ENGINE_LAMBDA_REGION: str = "us-east-1"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
