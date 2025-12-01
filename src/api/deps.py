from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from modules.users import (
    repository as user_repository,
    service as user_service,
    model as user_model,
)
from modules.auth import service as auth_service
from enums.token import TokenType

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_user_repository(db: AsyncSession = Depends(get_session)):
    return user_repository.UserRepository(db)


async def get_auth_service(
    repo: user_repository.UserRepository = Depends(get_user_repository),
):
    return auth_service.AuthService(repo)


async def get_user_service(
    user_repo: user_repository.UserRepository = Depends(get_user_repository),
    auth_svc: auth_service.AuthService = Depends(get_auth_service),
):
    return user_service.UserService(user_repo=user_repo, auth_svc=auth_svc)


async def get_authenticate_user(
    token: str = Depends(oauth2_scheme),
    auth_svc: auth_service.AuthService = Depends(get_auth_service),
) -> user_model.User:
    return await auth_svc.get_user_from_token(token=token, token_type=TokenType.ACCESS)
