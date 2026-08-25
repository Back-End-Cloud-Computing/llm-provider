from app.core.config import get_settings
from app.providers.factory import get_llm_provider
from app.providers.mock_provider import MockLLMProvider
from app.providers.openrouter_provider import OpenRouterLLMProvider


def test_defaults_to_mock_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    get_settings.cache_clear()
    assert isinstance(get_llm_provider(), MockLLMProvider)


def test_openrouter_selected_and_configured(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-key")
    get_settings.cache_clear()
    assert isinstance(get_llm_provider(), OpenRouterLLMProvider)


def test_openrouter_selected_without_key_falls_back_to_mock(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    get_settings.cache_clear()
    assert isinstance(get_llm_provider(), MockLLMProvider)
