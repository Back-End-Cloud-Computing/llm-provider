import pytest

from app.core.exceptions import LLMProviderError


@pytest.mark.asyncio
async def test_generate_returns_mock_text_by_default(api_client, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    from app.core.config import get_settings

    get_settings.cache_clear()

    response = await api_client.post("/generate", json={"prompt": "descreva um produto"})
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "mock"
    assert len(body["text"]) > 0


@pytest.mark.asyncio
async def test_generate_propagates_llm_provider_error(api_client, monkeypatch):
    import app.routes.generate as generate_route

    class _FailingProvider:
        name = "mock"

        async def generate_text(self, *args, **kwargs):
            raise LLMProviderError("boom")

    monkeypatch.setattr(generate_route, "get_llm_provider", lambda: _FailingProvider())

    response = await api_client.post("/generate", json={"prompt": "descreva um produto"})
    assert response.status_code == 502
    assert response.json()["error_type"] == "llm_provider_error"


@pytest.mark.asyncio
async def test_generate_rejects_empty_prompt(api_client):
    response = await api_client.post("/generate", json={"prompt": ""})
    assert response.status_code == 422
