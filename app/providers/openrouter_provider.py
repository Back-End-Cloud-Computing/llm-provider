import logging
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.exceptions import LLMProviderError
from app.providers.base import LLMProvider

logger = logging.getLogger(__name__)

# OpenRouter rejects a "models" array with more than 3 entries.
MAX_CANDIDATE_MODELS = 3


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
        order preserved), capped at OpenRouter's limit for the "models" array."""
        candidates = [model or self._default_model]
        for fallback in self._fallback_models:
            if fallback not in candidates:
                candidates.append(fallback)
        return candidates[:MAX_CANDIDATE_MODELS]

    def _payload(
        self,
        prompt: str,
        model: str | None,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        candidates = self._candidate_models(model)
        payload: dict[str, Any] = {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        # OpenRouter tries each model in "models" in order server-side, falling
        # back automatically on error/unavailability - a single model is sent
        # as "model" since "models" requires at least one alternative to matter.
        if len(candidates) > 1:
            payload["models"] = candidates
        else:
            payload["model"] = candidates[0]
        return payload

    async def generate_text(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 400,
    ) -> str:
        payload = self._payload(prompt, model, temperature, max_tokens)
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                logger.info("OpenRouter response served by model '%s'", data.get("model", "unknown"))
                content = data["choices"][0]["message"]["content"]
                if not isinstance(content, str) or not content.strip():
                    # Some free models return null/empty content (safety refusal,
                    # reasoning-only output, etc.) instead of an HTTP error.
                    logger.error("OpenRouter model '%s' returned no usable text content", data.get("model", "unknown"))
                    raise LLMProviderError(f"OpenRouter model returned no usable text content: {content!r}")
                return content.strip()
        except (httpx.HTTPError, KeyError, IndexError, TypeError) as exc:
            logger.error("OpenRouter request failed: %s", exc)
            raise LLMProviderError(f"OpenRouter request failed: {exc}") from exc
