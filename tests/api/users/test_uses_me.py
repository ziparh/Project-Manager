import pytest
import time_machine
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone

from modules.users.model import User as UserModel
from core.security.jwt_handler import JWTHandler
from enums.token import TokenType


@pytest.mark.asyncio
async def test_get_me_success(
    authenticated_client: AsyncClient,
    test_user: UserModel,
):
    response = await authenticated_client.get("api/v1/users/me")
    resp_data = response.json()

    assert response.status_code in (200, 201)
    assert resp_data['id'] == test_user.id
    assert resp_data['username'] == test_user.username
    assert "password" not in resp_data
    assert "hashed_password" not in resp_data

@pytest.mark.asyncio
async def test_get_me_without_access_token(client: AsyncClient):
    response = await client.get("api/v1/users/me")

    assert response.status_code == 401


@pytest.mark.integration
async def test_get_me_with_expired_token(
        client: AsyncClient,
        test_user: UserModel,
):

    past = datetime.now(timezone.utc) - timedelta(hours=24)

    with time_machine.travel(past):
        expired_token = JWTHandler.create(
            user_id=test_user.id,
            token_type=TokenType.ACCESS
        )

    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )

    assert response.status_code == 401
