from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from modules.users.repository import UserRepository
from modules.personal_tasks.repository import PersonalTaskRepository
from modules.projects.repository import ProjectRepository
from modules.project_members.repository import ProjectMemberRepository
from modules.project_tasks.repository import ProjectTaskRepository


async def get_user_repository(db: AsyncSession = Depends(get_session)):
    return UserRepository(db)


async def get_personal_task_repository(db: AsyncSession = Depends(get_session)):
    return PersonalTaskRepository(db)


async def get_project_repository(db: AsyncSession = Depends(get_session)):
    return ProjectRepository(db)


async def get_project_member_repository(db: AsyncSession = Depends(get_session)):
    return ProjectMemberRepository(db)


async def get_project_task_repository(db: AsyncSession = Depends(get_session)):
    return ProjectTaskRepository(db)
