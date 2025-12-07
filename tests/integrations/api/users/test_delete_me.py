import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio.session import AsyncSession

from modules.users.model import User as UserModel


@pytest.mark.integration
class TestDeleteMe:
    async def test_success(
        self,
        authenticated_client: AsyncClient,
        test_user: UserModel,
        db_session: AsyncSession,
    ):
        response = await authenticated_client.delete("api/v1/users/me")

        assert response.status_code == 204
        assert response.content == b""

        deleted_user = await db_session.get(UserModel, test_user.id)

        assert deleted_user is None

    async def test_invalid_token(
        self,
        client: AsyncClient,
        invalid_token: str,
    ):
        inv_token_headers = {"Authorization": f"Bearer {invalid_token}"}

        response = await client.delete(
            "api/v1/users/me",
            headers=inv_token_headers,
        )

        assert response.status_code == 401

    async def test_unauthorized(
        self,
        client: AsyncClient,
    ):
        response = await client.delete("api/v1/users/me")

        assert response.status_code == 401

    async def test_refresh_token_fail(
        self,
        client: AsyncClient,
        refresh_token: str,
    ):
        refresh_headers = {"Authorization": f"Bearer {refresh_token}"}

        response = await client.delete(
            "api/v1/users/me",
            headers=refresh_headers,
        )

        assert response.status_code == 401
