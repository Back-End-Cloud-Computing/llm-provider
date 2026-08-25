from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    model: str | None = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=400, ge=1, le=4000)


class GenerateResponse(BaseModel):
    text: str
    model: str
    provider: str
