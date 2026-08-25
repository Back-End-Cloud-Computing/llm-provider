from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application configuration, sourced from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "llm-provider"
    app_env: str = "development"
    log_level: str = "INFO"

    llm_provider: str = "mock"
    llm_model: str = "qwen/qwen3-8b:free"
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    llm_timeout_seconds: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
