from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jwt import InvalidTokenError

from core.security.password import PasswordHasher
from core.security.jwt_handler import JWTHandler
from . import schemas as auth_schemas
from modules.users import (
    repository as user_repository,
    model as user_model,
)
from enums.token import TokenType


class AuthService:
    def __init__(self, user_repo: user_repository.UserRepository):
        self.user_repo = user_repo

    async def get_user_from_token(
        self, token: str, token_type: TokenType
    ) -> user_model.User:
        inv_token_exc = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
        )
        try:
            payload = JWTHandler.decode(token=token)
        except InvalidTokenError:
            raise inv_token_exc

        if payload is None:
            raise inv_token_exc
        if payload.get("type") != token_type.value:
            raise inv_token_exc

        user_id = int(payload.get("sub"))
        db_user = await self.user_repo.get_user_by_id(user_id=user_id)

        if not db_user:
            raise inv_token_exc
        return db_user

    async def register_user(
        self, register_data: auth_schemas.UserRegister
    ) -> user_model.User:
        is_user = await self.user_repo.get_user_by_username(register_data.username)

        if is_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User {register_data.username} already exists.",
            )

        user_to_db = user_model.User(
            username=register_data.username,
            hashed_password=PasswordHasher.hash(register_data.password),
        )
        user = await self.user_repo.create_user(user=user_to_db)
        await self.user_repo.db.commit()

        return user

    async def login_user(
        self, login_data: OAuth2PasswordRequestForm
    ) -> auth_schemas.TokenResponse:
        db_user = await self._get_user_from_login_data(login_data=login_data)

        return self._create_tokens(user=db_user)

    async def refresh_access_token(
        self, refresh_token_request: auth_schemas.RefreshTokenRequest
    ) -> auth_schemas.TokenResponse:
        db_user = await self.get_user_from_token(
            token=refresh_token_request.refresh_token,
            token_type=TokenType.REFRESH,
        )

        return self._create_tokens(user=db_user)

    async def _get_user_from_login_data(
        self, login_data: OAuth2PasswordRequestForm
    ) -> user_model.User:
        wrong_auth_exc = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
        )
        db_user = await self.user_repo.get_user_by_username(login_data.username)

        if not db_user:
            raise wrong_auth_exc
        if not PasswordHasher.verify(
            password=login_data.password, hashed=db_user.hashed_password
        ):
            raise wrong_auth_exc
        return db_user

    @staticmethod
    def _create_tokens(user: user_model.User) -> auth_schemas.TokenResponse:
        access_token = JWTHandler.create(user_id=user.id, token_type=TokenType.ACCESS)
        refresh_token = JWTHandler.create(user_id=user.id, token_type=TokenType.REFRESH)

        return auth_schemas.TokenResponse(
            access_token=access_token, refresh_token=refresh_token
        )
