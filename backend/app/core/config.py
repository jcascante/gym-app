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

    # Database - automatically uses SQLite for dev, PostgreSQL for prod
    SQLITE_URL: str = "sqlite+aiosqlite:///./gym_app.db"
    POSTGRES_URL: str = "postgresql+asyncpg://user:password@localhost/gym_app"

    @property
    def DATABASE_URL(self) -> str:
        """Returns the appropriate database URL based on environment"""
        if self.ENVIRONMENT == "development":
            return self.SQLITE_URL
        return self.POSTGRES_URL

    @property
    def DATABASE_CONNECT_ARGS(self) -> dict:
        """Returns connection arguments specific to the database type"""
        if self.ENVIRONMENT == "development":
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
