import pytest
import time_machine
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from modules.users.model import User as UserModel
from core.security.jwt_handler import JWTHandler
from core.security.password import PasswordHasher
from core.config import settings
from enums.token import TokenType

from tests.factories import DBUserFactory


@pytest.fixture
async def test_user(db_session: AsyncSession) -> UserModel:
    """
    Create a test user with known credentials.

    Credentials:
    - Username: test_user
    - Password: TestPassword123!
    """
    user = DBUserFactory.build(
        username="test_user",
        hashed_password=PasswordHasher.hash("TestPassword123!"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


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
    Useful for testing token expiration handling.
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
    """ " Return an invalid JWT token for testing."""
    return "invalid.jwt.token"
