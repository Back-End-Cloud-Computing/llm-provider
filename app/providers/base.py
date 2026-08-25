from abc import ABC, abstractmethod
from typing import AsyncGenerator


class LLMProvider(ABC):
    """Abstraction over the external LLM.

    Keeping this behind an interface means the concrete provider (and its cost,
    availability, and latency characteristics) can be swapped via configuration
    without touching callers, and the service can run/test fully offline via
    `MockLLMProvider`. This service never contains business-specific prompts —
    callers always send a ready-made `prompt` string.
    """

    name: str = "base"

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 400,
    ) -> str:
        """Generate text from a prompt. Must raise LLMProviderError on failure."""

    @abstractmethod
    async def generate_text_stream(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 400,
    ) -> AsyncGenerator[str, None]:
        """Stream text chunks for a prompt. Must raise LLMProviderError on failure."""
        if False:  # pragma: no cover - makes this an async generator for type checkers
            yield ""
