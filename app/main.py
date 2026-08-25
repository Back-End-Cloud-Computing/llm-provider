from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import LLMProviderError
from app.core.logging import configure_logging
from app.routes import api_router


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        description=(
            "LLM Provider microservice: abstracts access to the underlying language "
            "model (OpenRouter or an offline mock). Carries no business-specific "
            "prompts — callers always send a ready-made prompt."
        ),
        version="1.0.0",
    )

    application.include_router(api_router)

    @application.exception_handler(LLMProviderError)
    async def llm_provider_error_handler(request: Request, exc: LLMProviderError) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": str(exc), "error_type": "llm_provider_error"})

    @application.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
