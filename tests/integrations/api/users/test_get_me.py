import pytest
from httpx import AsyncClient

from modules.users.model import User as UserModel


@pytest.mark.integration
async def test_get_me_success(
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


@pytest.mark.integration
async def test_get_me_without_token(client: AsyncClient):
    response = await client.get("api/v1/users/me")

    assert response.status_code == 401


@pytest.mark.integration
async def test_get_me_with_invalid_token(
    client: AsyncClient,
    invalid_token: str,
):
    invalid_headers = {"Authorization": f"Bearer {invalid_token}"}

    response = await client.get(
        "api/v1/users/me",
        headers=invalid_headers,
    )

    assert response.status_code == 401


@pytest.mark.integration
async def test_get_me_with_refresh_token_fail(
    client: AsyncClient,
    refresh_token: str,
):
    invalid_headers = {"Authorization": f"Bearer {refresh_token}"}

    response = await client.get(
        "api/v1/users/me",
        headers=invalid_headers,
    )

    assert response.status_code == 401


@pytest.mark.integration
async def test_get_me_with_expired_token(
    client: AsyncClient,
    expired_access_token: str,
):
    invalid_headers = {"Authorization": f"Bearer {expired_access_token}"}

    response = await client.get(
        "api/v1/users/me",
        headers=invalid_headers,
    )

    assert response.status_code == 401
