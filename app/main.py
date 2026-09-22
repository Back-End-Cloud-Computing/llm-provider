from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError, LLMProviderError
from app.core.logging import configure_logging
from app.core.security import get_current_user, load_public_key
from app.routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await load_public_key()
    yield


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
        lifespan=lifespan,
    )

    application.include_router(api_router, dependencies=[Depends(get_current_user)])

    @application.exception_handler(AuthenticationError)
    async def authentication_error_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
        return JSONResponse(status_code=401, content={"detail": str(exc), "error_type": "authentication_error"})

    @application.exception_handler(LLMProviderError)
    async def llm_provider_error_handler(request: Request, exc: LLMProviderError) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": str(exc), "error_type": "llm_provider_error"})

    @application.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
