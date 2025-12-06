from fastapi import Depends

from api.v1.deps.auth import get_auth_service
from api.v1.deps.repositories import get_users_repository
from modules.auth import service as auth_service
from modules.users import repository as user_repository, service as user_service


async def get_user_service(
    user_repo: user_repository.UserRepository = Depends(get_users_repository),
    auth_svc: auth_service.AuthService = Depends(get_auth_service),
):
    return user_service.UserService(user_repo=user_repo, auth_svc=auth_svc)
