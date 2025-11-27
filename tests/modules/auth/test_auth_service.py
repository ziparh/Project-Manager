import pytest
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from core.security.password import PasswordHasher
from core.security.jwt_handler import JWTHandler
from modules.users.repository import UserRepository
from modules.auth.service import AuthService
from modules.auth.schemas import RefreshTokenRequest
from enums.token import TokenType

from tests.factories import RegisterUserFactory, DBUserFactory


@pytest.fixture
def auth_service_with_mocks():
    mock_user_repo = AsyncMock(spec=UserRepository)
    mock_user_repo.db = AsyncMock(spec=AsyncSession)

    service = AuthService(user_repo=mock_user_repo)

    return service, mock_user_repo


@pytest.mark.asyncio
@patch.object(JWTHandler, "decode")
async def test_get_user_from_token_success(mock_decode, auth_service_with_mocks):
    service, mock_user_repo = auth_service_with_mocks
    user_id = 123
    token_type = TokenType.ACCESS
    token = "valid.jwt.token"

    mock_decode.return_value = {
        "type": token_type.value,
        "sub": str(user_id),
    }
    expected_user = DBUserFactory.build(id=user_id)
    mock_user_repo.get_user_by_id.return_value = expected_user

    db_user = await service.get_user_from_token(token=token, token_type=token_type)

    mock_decode.assert_called_once_with(token=token)
    mock_user_repo.get_user_by_id.assert_called_once_with(user_id=user_id)
    assert db_user == expected_user


@pytest.mark.asyncio
@patch.object(JWTHandler, "decode", side_effect=InvalidTokenError)
async def test_get_user_from_token_invalid_token(mock_decode, auth_service_with_mocks):
    service, _ = auth_service_with_mocks

    with pytest.raises(HTTPException) as exc_info:
        await service.get_user_from_token(
            token="test_token",
            token_type=TokenType.ACCESS,
        )
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Invalid token."


@pytest.mark.asyncio
@patch.object(JWTHandler, "decode")
@pytest.mark.parametrize(
    "decode_return, expected_details",
    [
        (None, "Invalid token."),
        ({"sub": "123", "type": "WRONG_TOKEN_TYPE"}, "Invalid token."),
    ],
    ids=["invalid_signature", "wrong_token_type"],
)
async def test_get_user_from_token_invalid_payload(
    mock_decode,
    auth_service_with_mocks,
    decode_return,
    expected_details,
):
    service, _ = auth_service_with_mocks
    mock_decode.return_value = decode_return

    with pytest.raises(HTTPException) as exc_info:
        await service.get_user_from_token(
            token="test",
            token_type=TokenType.ACCESS,
        )
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == expected_details


@pytest.mark.asyncio
@patch.object(PasswordHasher, "hash", return_value="fake-hashed-password")
async def test_register_user_success(mock_hash, auth_service_with_mocks):
    service, mock_user_repo = auth_service_with_mocks
    data_to_register = RegisterUserFactory.build()
    db_user_mock = DBUserFactory.build()

    mock_user_repo.get_user_by_username.return_value = None
    mock_user_repo.create_user.return_value = db_user_mock

    created_user = await service.register_user(data_to_register)

    mock_user_repo.get_user_by_username.assert_called_once_with(
        data_to_register.username
    )
    mock_hash.assert_called_once_with(data_to_register.password)
    mock_user_repo.create_user.assert_called_once()
    mock_user_repo.db.commit.assert_called_once()
    assert created_user == db_user_mock


@pytest.mark.asyncio
async def test_register_user_conflict(auth_service_with_mocks):
    service, mock_user_repo = auth_service_with_mocks
    data_to_register = RegisterUserFactory.build()

    mock_user_repo.get_user_by_username.return_value = data_to_register

    with pytest.raises(HTTPException) as exc_info:
        await service.register_user(data_to_register)

    assert exc_info.value.status_code == status.HTTP_409_CONFLICT
    mock_user_repo.create_user.assert_not_called()


@pytest.mark.asyncio
@patch.object(JWTHandler, "create")
@patch.object(PasswordHasher, "verify")
async def test_login_user_success(
    mock_password_verify, mock_jwt_create, auth_service_with_mocks
):
    service, mock_user_repo = auth_service_with_mocks
    login_data = OAuth2PasswordRequestForm(username="test_user", password="password123")
    db_user = DBUserFactory.build(username="test_user", hashed_password="password123")

    mock_user_repo.get_user_by_username.return_value = db_user
    mock_password_verify.return_value = True
    mock_jwt_create.side_effect = ["access.token.123", "refresh.token.456"]

    token_response = await service.login_user(login_data)

    mock_user_repo.get_user_by_username.assert_called_once_with(login_data.username)
    mock_password_verify.assert_called_once_with(
        password=login_data.password, hashed=db_user.hashed_password
    )
    assert mock_jwt_create.call_count == 2
    assert token_response.access_token == "access.token.123"
    assert token_response.refresh_token == "refresh.token.456"


@pytest.mark.asyncio
@patch.object(JWTHandler, "create")
@patch.object(PasswordHasher, "verify")
async def test_login_user_not_found(
    mock_password_verify, mock_jwt_create, auth_service_with_mocks
):
    service, mock_user_repo = auth_service_with_mocks
    login_data = OAuth2PasswordRequestForm(username="test_user", password="password123")

    mock_user_repo.get_user_by_username.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await service.login_user(login_data)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Incorrect username or password."
    mock_password_verify.assert_not_called()
    mock_jwt_create.assert_not_called()


@pytest.mark.asyncio
@patch.object(JWTHandler, "create")
@patch.object(PasswordHasher, "verify")
async def test_user_wrong_password(
    mock_password_verify, mock_jwt_create, auth_service_with_mocks
):
    service, mock_user_repo = auth_service_with_mocks
    login_data = OAuth2PasswordRequestForm(
        username="test_user", password="wrong_password"
    )
    db_user = DBUserFactory.build(username="test_user", hashed_password="password123")

    mock_user_repo.get_user_by_username.return_value = db_user
    mock_password_verify.return_value = False

    with pytest.raises(HTTPException) as exc_info:
        await service.login_user(login_data)

    mock_user_repo.get_user_by_username.assert_called_once_with(login_data.username)
    mock_password_verify.assert_called_once_with(
        password=login_data.password, hashed=db_user.hashed_password
    )
    mock_jwt_create.assert_not_called()
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Incorrect username or password."


@pytest.mark.asyncio
@patch.object(JWTHandler, "create")
@patch.object(AuthService, "get_user_from_token")
async def test_refresh_access_token_success(
    mock_get_user_from_token, mock_jwt_create, auth_service_with_mocks
):
    service, _ = auth_service_with_mocks
    refresh_req = RefreshTokenRequest(refresh_token="valid_refresh_token")
    user = DBUserFactory.build()

    mock_get_user_from_token.return_value = user
    mock_jwt_create.side_effect = ["access.token.123", "refresh.token.456"]

    token_response = await service.refresh_access_token(refresh_req)

    mock_get_user_from_token.assert_called_once_with(
        token=refresh_req.refresh_token, token_type=TokenType.REFRESH
    )
    assert mock_jwt_create.call_count == 2
    assert token_response.access_token == "access.token.123"
    assert token_response.refresh_token == "refresh.token.456"
