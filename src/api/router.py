from fastapi import APIRouter

from core.config import settings
from api.v1.router import router as api_v1_router

router = APIRouter()

router.include_router(api_v1_router, prefix=settings.prefix.api_v1)
