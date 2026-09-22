class LLMProviderServiceError(Exception):
    """Base exception for the llm-provider domain."""


class LLMProviderError(LLMProviderServiceError):
    """Raised when the external LLM provider fails, times out, or is not configured."""


class AuthenticationError(LLMProviderServiceError):
    """Raised when the incoming request's bearer token is missing, malformed, or
    fails local verification against the authorization service's public key."""
