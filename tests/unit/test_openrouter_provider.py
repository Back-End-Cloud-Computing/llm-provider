import json

import pytest
import respx
from httpx import Response

from app.core.config import get_settings
from app.core.exceptions import LLMProviderError
from app.providers.openrouter_provider import OpenRouterLLMProvider


def _configure(monkeypatch, api_key: str | None = "sk-test-key"):
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    if api_key is not None:
        monkeypatch.setenv("OPENROUTER_API_KEY", api_key)
    else:
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    get_settings.cache_clear()


def test_missing_api_key_raises(monkeypatch):
    _configure(monkeypatch, api_key=None)
    with pytest.raises(LLMProviderError):
        OpenRouterLLMProvider()


@pytest.mark.asyncio
@respx.mock
async def test_generate_text_success(monkeypatch):
    _configure(monkeypatch)
    settings = get_settings()
    respx.post(f"{settings.openrouter_base_url}/chat/completions").mock(
        return_value=Response(200, json={"choices": [{"message": {"content": "  ola mundo  "}}]})
    )

    provider = OpenRouterLLMProvider()
    text = await provider.generate_text("prompt qualquer")
    assert text == "ola mundo"


@pytest.mark.asyncio
@respx.mock
async def test_generate_text_http_error_raises_llm_provider_error(monkeypatch):
    _configure(monkeypatch)
    settings = get_settings()
    respx.post(f"{settings.openrouter_base_url}/chat/completions").mock(return_value=Response(500))

    provider = OpenRouterLLMProvider()
    with pytest.raises(LLMProviderError):
        await provider.generate_text("prompt qualquer")


@pytest.mark.asyncio
@respx.mock
async def test_generate_text_null_content_raises_llm_provider_error(monkeypatch):
    """Some free models return a 200 with `content: null` (safety refusal,
    reasoning-only output, etc.) instead of an HTTP error - this must not
    crash with an unhandled AttributeError on `.strip()`."""
    _configure(monkeypatch)
    settings = get_settings()
    respx.post(f"{settings.openrouter_base_url}/chat/completions").mock(
        return_value=Response(200, json={"choices": [{"message": {"content": None}}]})
    )

    provider = OpenRouterLLMProvider()
    with pytest.raises(LLMProviderError):
        await provider.generate_text("prompt qualquer")


@pytest.mark.asyncio
@respx.mock
async def test_generate_text_sends_models_fallback_array_by_default(monkeypatch):
    """With the default OPENROUTER_FALLBACK_MODELS configured, the primary model
    plus its fallbacks are sent as OpenRouter's "models" array, so OpenRouter
    itself falls back server-side if the primary is unavailable/discontinued."""
    _configure(monkeypatch)
    settings = get_settings()
    route = respx.post(f"{settings.openrouter_base_url}/chat/completions").mock(
        return_value=Response(200, json={"model": "openrouter/free", "choices": [{"message": {"content": "ok"}}]})
    )

    provider = OpenRouterLLMProvider()
    await provider.generate_text("prompt qualquer")

    body = json.loads(route.calls.last.request.content)
    assert "model" not in body
    assert body["models"][0] == settings.llm_model
    assert len(body["models"]) > 1


@pytest.mark.asyncio
@respx.mock
async def test_generate_text_caps_models_array_at_openrouter_limit(monkeypatch):
    """OpenRouter rejects a "models" array with more than 3 entries."""
    _configure(monkeypatch)
    monkeypatch.setenv("OPENROUTER_FALLBACK_MODELS", "a,b,c,d,e")
    get_settings.cache_clear()
    settings = get_settings()
    route = respx.post(f"{settings.openrouter_base_url}/chat/completions").mock(
        return_value=Response(200, json={"choices": [{"message": {"content": "ok"}}]})
    )

    provider = OpenRouterLLMProvider()
    await provider.generate_text("prompt qualquer")

    body = json.loads(route.calls.last.request.content)
    assert len(body["models"]) == 3


@pytest.mark.asyncio
@respx.mock
async def test_generate_text_sends_single_model_when_no_fallbacks_configured(monkeypatch):
    _configure(monkeypatch)
    monkeypatch.setenv("OPENROUTER_FALLBACK_MODELS", "")
    get_settings.cache_clear()
    settings = get_settings()
    route = respx.post(f"{settings.openrouter_base_url}/chat/completions").mock(
        return_value=Response(200, json={"choices": [{"message": {"content": "ok"}}]})
    )

    provider = OpenRouterLLMProvider()
    await provider.generate_text("prompt qualquer")

    body = json.loads(route.calls.last.request.content)
    assert "models" not in body
    assert body["model"] == settings.llm_model
