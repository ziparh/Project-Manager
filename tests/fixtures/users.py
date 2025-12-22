import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from core.security.password import PasswordHasher
from modules.users.model import User as UserModel
from tests.factories.models import UserModelFactory


@pytest.fixture
async def test_user(db_session: AsyncSession) -> UserModel:
    """
    Create a test user with known credentials.

    Credentials:
    - id: 123
    - Username: test_user
    - Email: test@google.com
    - Hashed_password: TestPassword123!
    """
    user = UserModelFactory.build(
        id=123,
        username="test_user",
        email="test@google.com",
        hashed_password=PasswordHasher.hash("TestPassword123!"),
    )
    db_session.add(user)
    await db_session.commit()

    return user


@pytest.fixture
async def other_user(db_session: AsyncSession) -> UserModel:
    """Create a secondary user for multi-user test scenarios."""
    user = UserModelFactory.build()
    db_session.add(user)
    await db_session.commit()

    return user
