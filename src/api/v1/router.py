from fastapi import APIRouter

from core.config import settings
from api.v1.routes.users import router as users_router
from api.v1.routes.auth import router as auth_router
from api.v1.routes.personal_tasks import router as personal_tasks_router
from api.v1.routes.projects import router as projects_router
from api.v1.routes.project_members import router as project_members_router
from api.v1.routes.project_tasks import router as project_tasks_router

router = APIRouter()

router.include_router(users_router, prefix=settings.prefix.users, tags=["users"])
router.include_router(auth_router, prefix=settings.prefix.auth, tags=["auth"])
router.include_router(
    personal_tasks_router,
    prefix=settings.prefix.personal_tasks,
    tags=["personal-tasks"],
)
router.include_router(
    projects_router, prefix=settings.prefix.projects, tags=["projects"]
)
router.include_router(
    project_members_router,
    prefix=settings.prefix.project_members,
    tags=["project-members"],
)
router.include_router(
    project_tasks_router,
    prefix=settings.prefix.project_tasks,
    tags=["project-tasks"],
)
