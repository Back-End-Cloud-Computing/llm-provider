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
async def test_generate_text_stream_yields_chunks(monkeypatch):
    _configure(monkeypatch)
    settings = get_settings()
    sse_body = (
        'data: {"choices": [{"delta": {"content": "ola "}}]}\n\n'
        'data: {"choices": [{"delta": {"content": "mundo"}}]}\n\n'
        "data: [DONE]\n\n"
    )
    respx.post(f"{settings.openrouter_base_url}/chat/completions").mock(
        return_value=Response(200, text=sse_body, headers={"content-type": "text/event-stream"})
    )

    provider = OpenRouterLLMProvider()
    chunks = [chunk async for chunk in provider.generate_text_stream("prompt qualquer")]
    assert "".join(chunks) == "ola mundo"
