import pytest

from app.providers.mock_provider import MockLLMProvider


@pytest.mark.asyncio
async def test_generate_text_returns_deterministic_text():
    provider = MockLLMProvider()
    text = await provider.generate_text("qualquer prompt")
    assert isinstance(text, str)
    assert len(text) > 0


@pytest.mark.asyncio
async def test_generate_text_stream_chunks_join_into_full_text():
    provider = MockLLMProvider()
    full_text = await provider.generate_text("qualquer prompt")

    chunks = [chunk async for chunk in provider.generate_text_stream("qualquer prompt")]
    assert len(chunks) >= 2
    assert "".join(chunks).strip() == full_text.strip()
