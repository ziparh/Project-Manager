from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from modules.users.repository import UserRepository
from modules.personal_tasks.repository import PersonalTaskRepository


async def get_users_repository(db: AsyncSession = Depends(get_session)):
    return UserRepository(db)


async def get_personal_tasks_repository(db: AsyncSession = Depends(get_session)):
    return PersonalTaskRepository(db)
