import json
import logging
from typing import Any, AsyncGenerator

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
        self._base_url = settings.openrouter_base_url
        self._api_key = settings.openrouter_api_key
        self._timeout = settings.llm_timeout_seconds

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _payload(
        self,
        prompt: str,
        model: str | None,
        temperature: float,
        max_tokens: int,
        stream: bool,
    ) -> dict[str, Any]:
        return {
            "model": model or self._default_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

    async def generate_text(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 400,
    ) -> str:
        payload = self._payload(prompt, model, temperature, max_tokens, stream=False)
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        except (httpx.HTTPError, KeyError, IndexError, TypeError) as exc:
            logger.error("OpenRouter request failed: %s", exc)
            raise LLMProviderError(f"OpenRouter request failed: {exc}") from exc

    async def generate_text_stream(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 400,
    ) -> AsyncGenerator[str, None]:
        payload = self._payload(prompt, model, temperature, max_tokens, stream=True)
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self._base_url}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line or not line.startswith("data:"):
                            continue
                        data_str = line[len("data:") :].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            event = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue
                        delta = event.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            yield content
        except (httpx.HTTPError, KeyError, IndexError, TypeError) as exc:
            logger.error("OpenRouter streaming request failed: %s", exc)
            raise LLMProviderError(f"OpenRouter streaming request failed: {exc}") from exc
