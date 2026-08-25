import logging

from app.core.config import get_settings
from app.core.exceptions import LLMProviderError
from app.providers.base import LLMProvider
from app.providers.mock_provider import MockLLMProvider
from app.providers.openrouter_provider import OpenRouterLLMProvider

logger = logging.getLogger(__name__)


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.llm_provider == "openrouter":
        try:
            return OpenRouterLLMProvider()
        except LLMProviderError:
            logger.warning("OpenRouter is not configured; falling back to MockLLMProvider")
            return MockLLMProvider()
    return MockLLMProvider()
