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
async def test_refresh_invalid_token(
    client: AsyncClient,
):
    refresh_request = RefreshTokenRequest(refresh_token="invalid.jwt.token")

    response = await client.post(
        "api/v1/auth/refresh",
        json=refresh_request.model_dump(),
    )

    assert response.status_code == 401
    assert "invalid token" in response.json()["detail"].lower()
