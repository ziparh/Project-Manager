import pytest
from httpx import AsyncClient

from tests.factories import RegisterUserFactory


@pytest.mark.integration
async def test_register_success(client: AsyncClient):
    data_to_register = RegisterUserFactory.build()

    response = await client.post(
        "/api/v1/auth/register",
        json=data_to_register.model_dump(),
    )
    resp_data = response.json()

    assert response.status_code in (200, 201)
    assert resp_data["username"] == data_to_register.username
    assert "password" not in resp_data
    assert "hashed_password" not in resp_data


@pytest.mark.integration
async def test_register_conflict(
    test_user,
    client: AsyncClient,
):
    data_to_register = RegisterUserFactory.build(username=test_user.username)

    response = await client.post(
        "/api/v1/auth/register",
        json=data_to_register.model_dump(),
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()


@pytest.mark.integration
@pytest.mark.parametrize(
    "invalid_data, expected_field",
    [
        ({"username": "ab", "password": "PassWord123!"}, "username"),
        ({"username": "testuser", "password": "123"}, "password"),
        ({"username": "", "password": "PassWord123!"}, "username"),
        ({"username": "testuser", "password": ""}, "password"),
        ({"password": "PassWord123!"}, "username"),
        ({"username": "testuser"}, "password"),
    ],
)
async def test_register_validation_errors(
    client: AsyncClient,
    invalid_data: dict,
    expected_field: str,
):
    response = await client.post("/api/v1/auth/register", json=invalid_data)
    errors = response.json()["detail"]

    assert response.status_code == 422
    assert any(expected_field in str(error["loc"]) for error in errors)
