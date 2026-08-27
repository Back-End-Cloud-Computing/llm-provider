from app.providers.base import LLMProvider

_MOCK_TEXT = (
    "Resposta gerada automaticamente em modo offline (nenhum provedor de LLM "
    "configurado ou disponivel no momento)."
)


class MockLLMProvider(LLMProvider):
    """Deterministic, offline fallback used when no LLM provider is configured,
    reachable, or when running tests. Never raises."""

    name = "mock"

    async def generate_text(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 400,
    ) -> str:
        return _MOCK_TEXT
