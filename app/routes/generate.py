import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import get_settings
from app.core.exceptions import LLMProviderError
from app.providers import get_llm_provider
from app.schemas.generate import GenerateRequest, GenerateResponse

logger = logging.getLogger(__name__)

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


@router.websocket("/generate/ws")
async def generate_ws(websocket: WebSocket) -> None:
    """Streams generated text chunks for a single prompt.

    Used exclusively by product-service's description-generation flow, which
    needs streaming; every other caller uses the plain POST /generate above.
    """
    await websocket.accept()
    settings = get_settings()
    try:
        raw_payload = await websocket.receive_text()
        payload = GenerateRequest.model_validate_json(raw_payload)

        provider = get_llm_provider()
        chunks: list[str] = []
        async for chunk in provider.generate_text_stream(
            payload.prompt,
            model=payload.model,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
        ):
            chunks.append(chunk)
            await websocket.send_json({"type": "chunk", "text": chunk})

        await websocket.send_json(
            {
                "type": "done",
                "text": "".join(chunks),
                "model": payload.model or settings.llm_model,
                "provider": provider.name,
            }
        )
    except WebSocketDisconnect:
        pass
    except LLMProviderError as exc:
        logger.error("Generate websocket failed: %s", exc)
        try:
            await websocket.send_json({"type": "error", "message": str(exc)})
        except Exception:  # noqa: BLE001 - connection may already be gone
            pass
    except Exception as exc:  # noqa: BLE001 - a malformed payload must not crash the connection silently
        logger.error("Generate websocket failed: %s", exc)
        try:
            await websocket.send_json({"type": "error", "message": "Erro ao gerar texto"})
        except Exception:  # noqa: BLE001
            pass
    finally:
        try:
            await websocket.close()
        except RuntimeError:
            pass
