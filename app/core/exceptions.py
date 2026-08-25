class LLMProviderServiceError(Exception):
    """Base exception for the llm-provider domain."""


class LLMProviderError(LLMProviderServiceError):
    """Raised when the external LLM provider fails, times out, or is not configured."""
