from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "SealCheck API"
    debug: bool = False

    # Database (required — set DATABASE_URL in .env)
    database_url: str

    # CORS
    cors_origins: list[str] = ["*"]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
