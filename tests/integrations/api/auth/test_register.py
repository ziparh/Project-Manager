import pytest
from httpx import AsyncClient

from tests.factories.schemas import UserRegisterFactory


@pytest.mark.integration
class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        data_to_register = UserRegisterFactory.build()

        response = await client.post(
            "/api/v1/auth/register",
            json=data_to_register.model_dump(),
        )
        resp_data = response.json()

        assert response.status_code in (200, 201)
        assert resp_data["username"] == data_to_register.username
        assert resp_data["email"] == data_to_register.email
        assert "password" not in resp_data
        assert "hashed_password" not in resp_data

    async def test_conflict_username(
        self,
        test_user,
        client: AsyncClient,
    ):
        data_to_register = UserRegisterFactory.build(username=test_user.username)

        response = await client.post(
            "/api/v1/auth/register",
            json=data_to_register.model_dump(),
        )

        assert response.status_code == 409
        assert "username already" in response.json()["detail"].lower()

    async def test_conflict_email(
        self,
        test_user,
        client: AsyncClient,
    ):
        data_to_register = UserRegisterFactory.build(email=test_user.email)

        response = await client.post(
            "/api/v1/auth/register",
            json=data_to_register.model_dump(),
        )

        assert response.status_code == 409
        assert "email already" in response.json()["detail"].lower()

    @pytest.mark.parametrize(
        "invalid_data, expected_field",
        [
            (
                {
                    "username": "ab",
                    "email": "test@google.com",
                    "password": "PassWord123!",
                },
                "username",
            ),
            (
                {
                    "username": "",
                    "email": "test@google.com",
                    "password": "PassWord123!",
                },
                "username",
            ),
            ({"email": "test@google.com", "password": "PassWord123!"}, "username"),
            (
                {
                    "username": "testuser",
                    "email": "wrong.google@com",
                    "password": "PassWord123!",
                },
                "email",
            ),
            (
                {"username": "testuser", "email": "", "password": "PassWord123!"},
                "email",
            ),
            ({"username": "testuser", "password": "PassWord123!"}, "email"),
            (
                {"username": "testuser", "email": "test@google.com", "password": "123"},
                "password",
            ),
            (
                {"username": "testuser", "email": "test@google.com", "password": ""},
                "password",
            ),
            ({"username": "testuser", "email": "test@google.com"}, "password"),
        ],
    )
    async def test_validation_errors(
        self,
        client: AsyncClient,
        invalid_data: dict,
        expected_field: str,
    ):
        response = await client.post("/api/v1/auth/register", json=invalid_data)
        errors = response.json()["detail"]

        assert response.status_code == 422
        assert any(expected_field in str(error["loc"]) for error in errors)
