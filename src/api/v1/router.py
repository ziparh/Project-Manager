from fastapi import APIRouter

from core.config import settings
from api.v1.endpoints.users import router as users_router

router = APIRouter()

router.include_router(users_router, prefix=settings.prefix.users, tags=["users"])