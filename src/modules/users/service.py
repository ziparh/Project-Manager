from . import repository as user_repository, model as user_model
from modules.auth import service as auth_service
from enums.token import TokenType


class UserService:
    def __init__(
        self,
        user_repo: user_repository.UserRepository,
        auth_svc: auth_service.AuthService,
    ):
        self.user_repo = user_repo
        self.auth_service = auth_svc

    async def get_users_me(self, token: str) -> user_model.User:
        db_user = await self.auth_service.get_user_from_token(
            token=token,
            token_type=TokenType.ACCESS,
        )

        return db_user
