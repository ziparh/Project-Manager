import pytest
from httpx import AsyncClient

from modules.users.model import User as UserModel


@pytest.mark.integration
class TestGetMe:
    async def test_success(
        self,
        authenticated_client: AsyncClient,
        test_user: UserModel,
    ):
        response = await authenticated_client.get("api/v1/users/me")
        resp_data = response.json()

        assert response.status_code in (200, 201)
        assert resp_data["id"] == test_user.id
        assert resp_data["username"] == test_user.username
        assert "password" not in resp_data
        assert "hashed_password" not in resp_data

    async def test_without_token(self, client: AsyncClient):
        response = await client.get("api/v1/users/me")

        assert response.status_code == 401

    async def test_with_invalid_token(
        self,
        client: AsyncClient,
        invalid_token: str,
    ):
        invalid_headers = {"Authorization": f"Bearer {invalid_token}"}

        response = await client.get(
            "api/v1/users/me",
            headers=invalid_headers,
        )

        assert response.status_code == 401

    async def test_with_refresh_token_fail(
        self,
        client: AsyncClient,
        refresh_token: str,
    ):
        invalid_headers = {"Authorization": f"Bearer {refresh_token}"}

        response = await client.get(
            "api/v1/users/me",
            headers=invalid_headers,
        )

        assert response.status_code == 401

    async def test_with_expired_token(
        self,
        client: AsyncClient,
        expired_access_token: str,
    ):
        invalid_headers = {"Authorization": f"Bearer {expired_access_token}"}

        response = await client.get(
            "api/v1/users/me",
            headers=invalid_headers,
        )

        assert response.status_code == 401
