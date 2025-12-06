from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from api.v1.deps.repositories import get_users_repository
from enums.token import TokenType
from modules.auth import service as auth_service
from modules.users import repository as user_repository, model as user_model

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_auth_service(
    repo: user_repository.UserRepository = Depends(get_users_repository),
):
    return auth_service.AuthService(repo)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_svc: auth_service.AuthService = Depends(get_auth_service),
) -> user_model.User:
    return await auth_svc.get_user_from_token(token=token, token_type=TokenType.ACCESS)
