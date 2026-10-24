from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application configuration, sourced from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "llm-provider"
    app_env: str = "development"
    log_level: str = "INFO"

    auth_service_base_url: str = "http://localhost:8081"

    llm_provider: str = "mock"
    llm_model: str = "nvidia/nemotron-3.5-lightning:free"
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    llm_timeout_seconds: int = 60

    # Comma-separated OpenRouter model ids tried, in order, after `llm_model`,
    # one request at a time (see OpenRouterLLMProvider.generate_text). A plain
    # HTTP error moves to the next candidate; so does a 200 with null/empty
    # content, which some free models return on a refusal or reasoning-only
    # output - OpenRouter's own "models" fallback array does NOT retry that
    # case, only outright request failures, so this is done client-side
    # instead. Free models get discontinued/renamed over time, so this exists
    # to survive any single one of them disappearing. "openrouter/free" (an
    # auto-router across whatever free model is up) is last: it works but
    # picks an arbitrary model, so named models are tried first.
    openrouter_fallback_models: str = (
        "nvidia/nemotron-3.5-super-vl:free,"
        "nvidia/nemotron-3-ultra-550b-a55b:free,"
        "dots-studio/dots-3-note-preview:free,"
        "openrouter/free"
    )

    openrouter_disable_reasoning: bool = True

    @property
    def openrouter_fallback_model_list(self) -> list[str]:
        return [model.strip() for model in self.openrouter_fallback_models.split(",") if model.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
