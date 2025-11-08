import jwt
from jwt import InvalidTokenError
from datetime import datetime, timedelta, timezone

from core.config import settings
from enums.token import TokenType


class JWTHandler:
    @staticmethod
    def create(user_id: int, token_type: TokenType) -> str:
        if token_type == TokenType.ACCESS:
            expire_seconds = settings.jwt.access_token_expire
        elif token_type == TokenType.REFRESH:
            expire_seconds = settings.jwt.refresh_token_expire
        else:
            raise ValueError(f"Invalid token_type: {token_type}")

        now = datetime.now(timezone.utc)
        expire = now + timedelta(seconds=expire_seconds)

        payload = {
            "type": token_type.value,
            "sub": str(user_id),
            "iat": now.timestamp(),
            "exp": expire.timestamp(),
        }

        token = jwt.encode(
            payload, settings.jwt.secret_key, algorithm=settings.jwt.algorithm
        )
        return token

    @staticmethod
    def decode(token: str) -> dict | None:
        try:
            decoded = jwt.decode(
                token, settings.jwt.secret_key, algorithms=[settings.jwt.algorithm]
            )
            return decoded
        except InvalidTokenError:
            return None
