import logging
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.exceptions import LLMProviderError
from app.providers.base import LLMProvider

logger = logging.getLogger(__name__)


class OpenRouterLLMProvider(LLMProvider):
    """Calls the OpenRouter chat-completions API (OpenAI-compatible)."""

    name = "openrouter"

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.openrouter_api_key:
            raise LLMProviderError("OPENROUTER_API_KEY is not configured")
        self._default_model = settings.llm_model
        self._fallback_models = settings.openrouter_fallback_model_list
        self._base_url = settings.openrouter_base_url
        self._api_key = settings.openrouter_api_key
        self._timeout = settings.llm_timeout_seconds

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _candidate_models(self, model: str | None) -> list[str]:
        """The requested model first, then the configured fallbacks (deduped,
        order preserved)."""
        candidates = [model or self._default_model]
        for fallback in self._fallback_models:
            if fallback not in candidates:
                candidates.append(fallback)
        return candidates

    def _payload(self, prompt: str, model: str, temperature: float, max_tokens: int) -> dict[str, Any]:
        return {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

    async def _generate_with_model(
        self, client: httpx.AsyncClient, model: str, prompt: str, temperature: float, max_tokens: int
    ) -> str:
        payload = self._payload(prompt, model, temperature, max_tokens)
        try:
            response = await client.post(f"{self._base_url}/chat/completions", headers=self._headers(), json=payload)
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise LLMProviderError(f"OpenRouter request to model '{model}' failed: {exc}") from exc

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError(f"OpenRouter model '{model}' returned an unexpected response shape") from exc

        if not isinstance(content, str) or not content.strip():
            # Some free models return null/empty content on a 200 (safety
            # refusal, reasoning-only output, etc.) - not an HTTP error, so
            # OpenRouter's own routing has no reason to pick another model.
            raise LLMProviderError(f"OpenRouter model '{model}' returned no usable text content")

        return content.strip()

    async def generate_text(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 400,
    ) -> str:
        candidates = self._candidate_models(model)
        last_error: LLMProviderError | None = None

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for candidate in candidates:
                try:
                    text = await self._generate_with_model(client, candidate, prompt, temperature, max_tokens)
                    logger.info("OpenRouter response served by model '%s'", candidate)
                    return text
                except LLMProviderError as exc:
                    logger.warning("Candidate model '%s' failed, trying next: %s", candidate, exc)
                    last_error = exc

        logger.error("All OpenRouter candidate models failed: %s", candidates)
        raise last_error
