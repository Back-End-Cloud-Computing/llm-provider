from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application configuration, sourced from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "llm-provider"
    app_env: str = "development"
    log_level: str = "INFO"

    llm_provider: str = "mock"
    llm_model: str = "google/gemma-4-26b-a4b-it:free"
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    llm_timeout_seconds: int = 60

    # Comma-separated OpenRouter model ids tried, in order, after `llm_model`,
    # via OpenRouter's own "models" fallback array - it moves to the next one
    # server-side on error/unavailability, so no client-side retry loop is
    # needed here. Free models get discontinued/renamed over time, so this
    # exists to survive any single one of them disappearing. "openrouter/free"
    # (an auto-router across whatever free model is up) is last: it works but
    # picks an arbitrary model, so named models are tried first.
    # OpenRouter caps the "models" array at 3 entries total (see MAX_CANDIDATE_MODELS
    # in the OpenRouter provider), so only the first 2 fallbacks here ever matter
    # alongside `llm_model`.
    openrouter_fallback_models: str = "minimax/minimax-m2.7:free,openrouter/free"

    @property
    def openrouter_fallback_model_list(self) -> list[str]:
        return [model.strip() for model in self.openrouter_fallback_models.split(",") if model.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
