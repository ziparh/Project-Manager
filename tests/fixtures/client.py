import pytest
from httpx import AsyncClient, ASGITransport
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from main import app
from db.session import get_session


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTP client for API testing."""

    async def _override_get_session():
        """Override database dependency to use test session."""
        yield db_session

    app.dependency_overrides[get_session] = _override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def authenticated_client(
    client: AsyncClient,
    access_token: str,
) -> AsyncClient:
    """Provide an HTTP client with authentication headers set."""
    client.headers["Authorization"] = f"Bearer {access_token}"

    return client
