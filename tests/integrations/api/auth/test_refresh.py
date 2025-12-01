import pytest
from httpx import AsyncClient

from modules.auth.schemas import RefreshTokenRequest


@pytest.mark.integration
async def test_refresh_access(
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


@pytest.mark.integration
async def test_refresh_with_access_token(
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


@pytest.mark.integration
async def test_refresh_invalid_token(
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


@pytest.mark.integration
async def test_refresh_without_token(client: AsyncClient):
    response = await client.post(
        "api/v1/auth/refresh",
        json={},
    )

    assert response.status_code == 422


@pytest.mark.integration
async def test_refresh_with_expired_token(
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
