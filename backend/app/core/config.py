from pydantic_settings import BaseSettings
from typing import List, Literal


class Settings(BaseSettings):
    PROJECT_NAME: str = "Gym App API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Environment
    ENVIRONMENT: Literal["development", "production"] = "development"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

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

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
