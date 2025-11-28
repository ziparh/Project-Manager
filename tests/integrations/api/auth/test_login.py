import pytest
from httpx import AsyncClient

from core.security.jwt_handler import JWTHandler
from enums.token import TokenType


@pytest.mark.integration
async def test_login_success(
    test_user,
    client: AsyncClient,
):
    password = "TestPassword123!"  # password for test_user

    response = await client.post(
        "api/v1/auth/login",
        data={"username": test_user.username, "password": password},
    )
    resp_data = response.json()

    assert response.status_code in (200, 201)
    assert "access_token" in resp_data
    assert "refresh_token" in resp_data
    assert resp_data["token_type"] == "bearer"

    access_token = JWTHandler.decode(resp_data["access_token"])
    refresh_token = JWTHandler.decode(resp_data["refresh_token"])

    assert access_token["sub"] == str(test_user.id)
    assert refresh_token["sub"] == str(test_user.id)
    assert access_token["type"] == TokenType.ACCESS.value
    assert refresh_token["type"] == TokenType.REFRESH.value


@pytest.mark.integration
async def test_login_wrong_password(
    test_user,
    client: AsyncClient,
):
    response = await client.post(
        "api/v1/auth/login",
        data={"username": test_user.username, "password": "WrongPassword123!"},
    )

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.integration
async def test_login_not_exists_user(client: AsyncClient):
    response = await client.post(
        "api/v1/auth/login",
        data={"username": "nonexistent_user", "password": "SomePassword123!"},
    )

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


SQL_INJECTION_PAYLOADS = [
    "' OR '1'='1",
    "' OR '1'='1' --",
    "admin' --",
    "'; DROP TABLE users; --",
    "' UNION SELECT 1, 'admin', 'password' --",
]


@pytest.mark.integration
@pytest.mark.parametrize("malicious_input", SQL_INJECTION_PAYLOADS)
async def test_login_sql_injection_username(
    client: AsyncClient,
    malicious_input: str,
):
    response = await client.post(
        "api/v1/auth/login",
        data={"username": malicious_input, "password": "AnyPassword123!"},
    )

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.integration
@pytest.mark.parametrize("malicious_input", SQL_INJECTION_PAYLOADS)
async def test_login_sql_injection_password(
    test_user,
    client: AsyncClient,
    malicious_input: str,
):
    response = await client.post(
        "api/v1/auth/login",
        data={"username": test_user.username, "password": malicious_input},
    )

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()
