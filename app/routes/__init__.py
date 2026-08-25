from fastapi import APIRouter

from app.routes.generate import router as generate_router

api_router = APIRouter()
api_router.include_router(generate_router)

__all__ = ["api_router"]
