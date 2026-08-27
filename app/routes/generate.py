from fastapi import APIRouter

from app.core.config import get_settings
from app.providers import get_llm_provider
from app.schemas.generate import GenerateRequest, GenerateResponse

router = APIRouter(tags=["generate"])


@router.post("/generate", response_model=GenerateResponse)
async def generate(payload: GenerateRequest) -> GenerateResponse:
    settings = get_settings()
    provider = get_llm_provider()
    text = await provider.generate_text(
        payload.prompt,
        model=payload.model,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
    )
    return GenerateResponse(text=text, model=payload.model or settings.llm_model, provider=provider.name)
