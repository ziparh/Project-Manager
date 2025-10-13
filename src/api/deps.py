from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from modules.users import repository, service


async def get_user_repository(db: AsyncSession = Depends(get_session)):
    return repository.UserRepository(db)


async def get_user_service(repo: service.UserService = Depends(get_user_repository)):
    return service.UserService(repo)
