import pytest
from httpx import AsyncClient

from modules.auth.schemas import RefreshTokenRequest


@pytest.mark.integration
class TestRefresh:
    async def test_refresh_access(
        self,
        client: AsyncClient,
        refresh_token: str,
    ):
        refresh_request = RefreshTokenRequest(refresh_token=refresh_token)

        response = await client.post(
            "api/v1/auth/refresh",
            json=refresh_request.model_dump(),
        )
        resp_data = response.json()

        assert response.status_code in (200, 201)
        assert "access_token" in resp_data
        assert "refresh_token" in resp_data
        assert resp_data["token_type"] == "bearer"

    async def test_refresh_with_access_token(
        self,
        client: AsyncClient,
        access_token: str,
    ):
        refresh_request = RefreshTokenRequest(refresh_token=access_token)

        response = await client.post(
            "api/v1/auth/refresh",
            json=refresh_request.model_dump(),
        )

        assert response.status_code == 401
        assert "invalid token" in response.json()["detail"].lower()

    async def test_with_invalid_token(
        self,
        client: AsyncClient,
        invalid_token: str,
    ):
        refresh_request = RefreshTokenRequest(refresh_token=invalid_token)

        response = await client.post(
            "api/v1/auth/refresh",
            json=refresh_request.model_dump(),
        )

        assert response.status_code == 401
        assert "invalid token" in response.json()["detail"].lower()

    async def test_without_token(self, client: AsyncClient):
        response = await client.post(
            "api/v1/auth/refresh",
            json={},
        )

        assert response.status_code == 422

    async def test_with_expired_token(
        self,
        client: AsyncClient,
        expired_refresh_token: str,
    ):
        refresh_request = RefreshTokenRequest(refresh_token=expired_refresh_token)

        response = await client.post(
            "api/v1/auth/refresh",
            json=refresh_request.model_dump(),
        )

        assert response.status_code == 401
        assert "invalid token" in response.json()["detail"].lower()
