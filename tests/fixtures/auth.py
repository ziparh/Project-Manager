import pytest
import time_machine
from datetime import datetime, timedelta, timezone

from modules.users.model import User as UserModel
from core.security.jwt_handler import JWTHandler
from core.config import settings
from enums.token import TokenType


@pytest.fixture
def access_token(test_user: UserModel) -> str:
    """Generate a valid access token for the test user."""
    return JWTHandler.create(
        user_id=test_user.id,
        token_type=TokenType.ACCESS,
    )


@pytest.fixture
def refresh_token(test_user: UserModel) -> str:
    """Generate a valid refresh token for the test user."""
    return JWTHandler.create(
        user_id=test_user.id,
        token_type=TokenType.REFRESH,
    )


def create_expired_token(
    user: UserModel,
    token_type: TokenType,
    lifetime_in_seconds: int,
) -> str:
    """
    Helping function
    Generate an expired token.
    Useful for testing expired tokens.
    """
    expired_time = timedelta(seconds=lifetime_in_seconds + 1)

    past = datetime.now(timezone.utc) - expired_time

    with time_machine.travel(past, tick=False):
        return JWTHandler.create(
            user_id=user.id,
            token_type=token_type,
        )


@pytest.fixture
def expired_access_token(test_user: UserModel) -> str:
    return create_expired_token(
        user=test_user,
        token_type=TokenType.ACCESS,
        lifetime_in_seconds=settings.jwt.access_token_expire,
    )


@pytest.fixture
def expired_refresh_token(test_user: UserModel) -> str:
    return create_expired_token(
        user=test_user,
        token_type=TokenType.REFRESH,
        lifetime_in_seconds=settings.jwt.refresh_token_expire,
    )


@pytest.fixture
def invalid_token() -> str:
    """Return an invalid JWT token for testing."""
    return "invalid.jwt.token"
