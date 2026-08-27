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
async def test_generate_text_uses_only_primary_when_no_fallbacks_configured(monkeypatch):
    _configure(monkeypatch)
    monkeypatch.setenv("OPENROUTER_FALLBACK_MODELS", "")
    get_settings.cache_clear()
    settings = get_settings()
    route = respx.post(f"{settings.openrouter_base_url}/chat/completions").mock(
        return_value=Response(200, json={"choices": [{"message": {"content": "ok"}}]})
    )

    provider = OpenRouterLLMProvider()
    await provider.generate_text("prompt qualquer")

    assert route.call_count == 1
    body = json.loads(route.calls.last.request.content)
    assert body["model"] == settings.llm_model


@pytest.mark.asyncio
@respx.mock
async def test_generate_text_falls_back_to_next_model_on_http_error(monkeypatch):
    _configure(monkeypatch)
    monkeypatch.setenv("OPENROUTER_FALLBACK_MODELS", "fallback-model")
    get_settings.cache_clear()
    settings = get_settings()

    route = respx.post(f"{settings.openrouter_base_url}/chat/completions")
    route.side_effect = [
        Response(429),
        Response(200, json={"choices": [{"message": {"content": "resposta do fallback"}}]}),
    ]

    provider = OpenRouterLLMProvider()
    text = await provider.generate_text("prompt qualquer")

    assert text == "resposta do fallback"
    assert route.call_count == 2
    first_body = json.loads(route.calls[0].request.content)
    second_body = json.loads(route.calls[1].request.content)
    assert first_body["model"] == settings.llm_model
    assert second_body["model"] == "fallback-model"


@pytest.mark.asyncio
@respx.mock
async def test_generate_text_falls_back_to_next_model_on_empty_content(monkeypatch):
    """A 200 with null/empty content (safety refusal, reasoning-only output,
    etc.) is not an HTTP error, so it must still trigger our own move to the
    next candidate - OpenRouter's server-side fallback would not catch this."""
    _configure(monkeypatch)
    monkeypatch.setenv("OPENROUTER_FALLBACK_MODELS", "fallback-model")
    get_settings.cache_clear()

    route = respx.post(f"{get_settings().openrouter_base_url}/chat/completions")
    route.side_effect = [
        Response(200, json={"choices": [{"message": {"content": None}}]}),
        Response(200, json={"choices": [{"message": {"content": "resposta do fallback"}}]}),
    ]

    provider = OpenRouterLLMProvider()
    text = await provider.generate_text("prompt qualquer")

    assert text == "resposta do fallback"
    assert route.call_count == 2


@pytest.mark.asyncio
@respx.mock
async def test_generate_text_raises_after_every_candidate_fails(monkeypatch):
    _configure(monkeypatch)
    monkeypatch.setenv("OPENROUTER_FALLBACK_MODELS", "fallback-model")
    get_settings.cache_clear()

    route = respx.post(f"{get_settings().openrouter_base_url}/chat/completions")
    route.mock(return_value=Response(500))

    provider = OpenRouterLLMProvider()
    with pytest.raises(LLMProviderError):
        await provider.generate_text("prompt qualquer")

    assert route.call_count == 2
