import pytest
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jwt import InvalidTokenError
from unittest.mock import AsyncMock, patch

from core.security.password import PasswordHasher
from core.security.jwt_handler import JWTHandler
from modules.users.repository import UserRepository
from modules.auth.service import AuthService
from modules.auth.schemas import RefreshTokenRequest
from enums.token import TokenType

from tests.factories.models import UserModelFactory
from tests.factories.schemas import UserRegisterFactory


@pytest.fixture
def mock_user_repo():
    """Mock users repository"""
    return AsyncMock(spec=UserRepository)


@pytest.fixture
def auth_svc(mock_user_repo):
    """Auth service with mocked repository"""
    return AuthService(user_repo=mock_user_repo)


@pytest.mark.unit
class TestGetUserFromToken:
    @patch.object(JWTHandler, "decode")
    async def test_success(self, mock_decode, auth_svc, mock_user_repo):
        user_id = 123
        token_type = TokenType.ACCESS
        token = "valid.jwt.token"

        mock_decode.return_value = {
            "type": token_type.value,
            "sub": str(user_id),
        }
        expected_user = UserModelFactory.build(id=user_id)
        mock_user_repo.get_by_id.return_value = expected_user

        db_user = await auth_svc.get_user_from_token(token=token, token_type=token_type)

        mock_decode.assert_called_once_with(token=token)
        mock_user_repo.get_by_id.assert_called_once_with(user_id=user_id)
        assert db_user == expected_user

    @patch.object(JWTHandler, "decode", side_effect=InvalidTokenError)
    async def test_invalid_token(self, mock_decode, auth_svc):
        with pytest.raises(HTTPException) as exc_info:
            await auth_svc.get_user_from_token(
                token="test_token",
                token_type=TokenType.ACCESS,
            )
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid token."

    @patch.object(JWTHandler, "decode")
    @pytest.mark.parametrize(
        "decode_return, expected_details",
        [
            (None, "Invalid token."),
            ({"sub": "123", "type": "WRONG_TOKEN_TYPE"}, "Invalid token."),
        ],
        ids=["invalid_signature", "wrong_token_type"],
    )
    async def test_invalid_payload(
        self,
        mock_decode,
        auth_svc,
        decode_return,
        expected_details,
    ):
        mock_decode.return_value = decode_return

        with pytest.raises(HTTPException) as exc_info:
            await auth_svc.get_user_from_token(
                token="test",
                token_type=TokenType.ACCESS,
            )
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == expected_details


@pytest.mark.unit
class TestRegister:
    @patch.object(PasswordHasher, "hash", return_value="fake-hashed-password")
    async def test_success(self, mock_hash, auth_svc, mock_user_repo):
        data_to_register = UserRegisterFactory.build()
        db_user_mock = UserModelFactory.build()

        mock_user_repo.get_by_username_or_email.return_value = None
        mock_user_repo.create.return_value = db_user_mock

        created_user = await auth_svc.register(data_to_register)

        mock_user_repo.get_by_username_or_email.assert_called_once_with(
            username=data_to_register.username,
            email=data_to_register.email,
        )
        mock_hash.assert_called_once_with(data_to_register.password)
        mock_user_repo.create.assert_called_once()
        assert created_user == db_user_mock

    async def test_conflict(self, auth_svc, mock_user_repo):
        data_to_register = UserRegisterFactory.build()

        mock_user_repo.get_by_username_or_email.return_value = data_to_register

        with pytest.raises(HTTPException) as exc_info:
            await auth_svc.register(data_to_register)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        mock_user_repo.create.assert_not_called()


@pytest.mark.unit
class TestLogin:
    @pytest.mark.unit
    @patch.object(JWTHandler, "create")
    @patch.object(PasswordHasher, "verify")
    async def test_success(
        self, mock_password_verify, mock_jwt_create, auth_svc, mock_user_repo
    ):
        login_data = OAuth2PasswordRequestForm(
            username="test_user", password="password123"
        )
        db_user = UserModelFactory.build(
            username="test_user", hashed_password="password123"
        )

        mock_user_repo.get_by_username.return_value = db_user
        mock_password_verify.return_value = True
        mock_jwt_create.side_effect = ["access.token.123", "refresh.token.456"]

        token_response = await auth_svc.login(login_data)

        mock_user_repo.get_by_username.assert_called_once_with(login_data.username)
        mock_password_verify.assert_called_once_with(
            password=login_data.password, hashed=db_user.hashed_password
        )
        assert mock_jwt_create.call_count == 2
        assert token_response.access_token == "access.token.123"
        assert token_response.refresh_token == "refresh.token.456"

    @pytest.mark.unit
    @patch.object(JWTHandler, "create")
    @patch.object(PasswordHasher, "verify")
    async def test_not_found(
        self, mock_password_verify, mock_jwt_create, auth_svc, mock_user_repo
    ):
        login_data = OAuth2PasswordRequestForm(
            username="test_user", password="password123"
        )

        mock_user_repo.get_by_username.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await auth_svc.login(login_data)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Incorrect username or password."
        mock_password_verify.assert_not_called()
        mock_jwt_create.assert_not_called()

    @pytest.mark.unit
    @patch.object(JWTHandler, "create")
    @patch.object(PasswordHasher, "verify")
    async def test_wrong_password(
        self, mock_password_verify, mock_jwt_create, auth_svc, mock_user_repo
    ):
        login_data = OAuth2PasswordRequestForm(
            username="test_user", password="wrong_password"
        )
        db_user = UserModelFactory.build(
            username="test_user", hashed_password="password123"
        )

        mock_user_repo.get_by_username.return_value = db_user
        mock_password_verify.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await auth_svc.login(login_data)

        mock_user_repo.get_by_username.assert_called_once_with(login_data.username)
        mock_password_verify.assert_called_once_with(
            password=login_data.password, hashed=db_user.hashed_password
        )
        mock_jwt_create.assert_not_called()
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Incorrect username or password."


@pytest.mark.unit
class TestRefresh:
    @pytest.mark.unit
    @patch.object(JWTHandler, "create")
    @patch.object(AuthService, "get_user_from_token")
    async def test_success(self, mock_get_user_from_token, mock_jwt_create, auth_svc):
        refresh_req = RefreshTokenRequest(refresh_token="valid_refresh_token")
        user = UserModelFactory.build()

        mock_get_user_from_token.return_value = user
        mock_jwt_create.side_effect = ["access.token.123", "refresh.token.456"]

        token_response = await auth_svc.refresh_tokens(refresh_req)

        mock_get_user_from_token.assert_called_once_with(
            token=refresh_req.refresh_token, token_type=TokenType.REFRESH
        )
        assert mock_jwt_create.call_count == 2
        assert token_response.access_token == "access.token.123"
        assert token_response.refresh_token == "refresh.token.456"
