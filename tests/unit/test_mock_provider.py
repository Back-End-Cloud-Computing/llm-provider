import pytest

from app.providers.mock_provider import MockLLMProvider


@pytest.mark.asyncio
async def test_generate_text_returns_deterministic_text():
    provider = MockLLMProvider()
    text = await provider.generate_text("qualquer prompt")
    assert isinstance(text, str)
    assert len(text) > 0
