from fastapi import APIRouter

from core.config import settings
from api.v1.endpoints.users import router as users_router
from api.v1.endpoints.auth import router as auth_router
from api.v1.endpoints.personal_tasks import router as personal_tasks_router

router = APIRouter()

router.include_router(users_router, prefix=settings.prefix.users, tags=["users"])
router.include_router(auth_router, prefix=settings.prefix.auth, tags=["auth"])
router.include_router(
    personal_tasks_router,
    prefix=settings.prefix.personal_tasks,
    tags=["personal-tasks"],
)
