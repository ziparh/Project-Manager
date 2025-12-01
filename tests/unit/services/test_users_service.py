import pytest
from fastapi import HTTPException, status
from unittest.mock import AsyncMock, patch

from modules.users import (
    repository as user_repository,
    service as user_service,
    schemas as user_schemas,
)
from modules.auth import service as auth_service
from core.security.password import PasswordHasher
from enums.token import TokenType

from tests.factories import DBUserFactory


@pytest.fixture
def user_service_with_mocks():
    mock_user_repo = AsyncMock(spec=user_repository.UserRepository)
    mock_auth_svc = AsyncMock(spec=auth_service.AuthService)

    user_svc = user_service.UserService(mock_user_repo, mock_auth_svc)

    return user_svc, mock_auth_svc, mock_user_repo


@pytest.mark.unit
async def test_get_me_success(user_service_with_mocks):
    user_svc, mock_auth_svc, _ = user_service_with_mocks
    test_token = "valid.jwt.token"
    expected_user = DBUserFactory.build()

    mock_auth_svc.get_user_from_token.return_value = expected_user

    db_user = await user_svc.get_me(token=test_token)

    mock_auth_svc.get_user_from_token.assert_called_once_with(
        token=test_token,
        token_type=TokenType.ACCESS,
    )
    assert db_user == expected_user


@pytest.mark.unit
async def test_get_me_invalid_token(user_service_with_mocks):
    user_svc, mock_auth_svc, _ = user_service_with_mocks

    mock_auth_svc.get_user_from_token.side_effect = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token.",
    )

    with pytest.raises(HTTPException) as exc_info:
        await user_svc.get_me(token="invalid.jwt.token")

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.unit
async def test_update_me_one_field_success(user_service_with_mocks):
    user_svc, mock_auth_svc, mock_user_repo = user_service_with_mocks
    mock_user = DBUserFactory.build()
    update_data = user_schemas.UserPatch(username="newusername")
    token = "valid.jwt.token"

    mock_auth_svc.get_user_from_token.return_value = mock_user
    mock_user_repo.get_by_username.return_value = None
    mock_user_repo.update_by_id.return_value = mock_user

    result = await user_svc.update_me(update_data, token)

    assert result == mock_user
    mock_user_repo.get_by_username.assert_called_once_with("newusername")
    mock_user_repo.update_by_id.assert_called_once()


@pytest.mark.unit
async def test_update_me_multiple_fields_success(user_service_with_mocks):
    user_svc, mock_auth_svc, mock_user_repo = user_service_with_mocks
    mock_user = DBUserFactory.build()
    update_data = user_schemas.UserPatch(
        username="newusername",
        email="new@example.com",
    )
    token = "valid.jwt.token"

    mock_auth_svc.get_user_from_token.return_value = mock_user
    mock_user_repo.get_by_username.return_value = None
    mock_user_repo.get_by_email.return_value = None
    mock_user_repo.update_by_id.return_value = mock_user

    result = await user_svc.update_me(update_data, token)

    assert result == mock_user
    mock_user_repo.get_by_username.assert_called_once_with(update_data.username)
    mock_user_repo.get_by_email.assert_called_once_with(update_data.email)
    mock_user_repo.update_by_id.assert_called_once()


@pytest.mark.unit
@patch.object(PasswordHasher, "hash", return_value="hashed-password")
async def test_update_me_password_hashed(mock_hash, user_service_with_mocks):
    user_svc, mock_auth_svc, mock_user_repo = user_service_with_mocks
    mock_user = DBUserFactory.build()
    update_data = user_schemas.UserPatch(password="newpassword123")
    token = "valid.jwt.token"

    mock_auth_svc.get_user_from_token.return_value = mock_user
    mock_user_repo.update_by_id.return_value = mock_user

    await user_svc.update_me(update_data, token)

    mock_hash.assert_called_once_with(update_data.password)
    mock_user_repo.update_by_id.assert_called_once_with(
        user_id=mock_user.id, update_data={"hashed_password": "hashed-password"}
    )


@pytest.mark.unit
async def test_update_me_username_conflict_username(user_service_with_mocks):
    user_svc, mock_auth_svc, mock_user_repo = user_service_with_mocks
    mock_user = DBUserFactory.build()
    update_data = user_schemas.UserPatch(username="taken")
    second_mock_user = DBUserFactory.build(username=update_data.username)
    token = "valid.jwt.token"

    mock_auth_svc.get_user_from_token.return_value = mock_user
    mock_user_repo.get_by_username.return_value = second_mock_user

    with pytest.raises(HTTPException) as exc_info:
        await user_svc.update_me(update_data, token)

    assert exc_info.value.status_code == status.HTTP_409_CONFLICT
    assert "Username already taken" in exc_info.value.detail
    mock_user_repo.update_by_id.assert_not_called()


@pytest.mark.unit
async def test_update_me_username_conflict_email(user_service_with_mocks):
    user_svc, mock_auth_svc, mock_user_repo = user_service_with_mocks
    mock_user = DBUserFactory.build()
    update_data = user_schemas.UserPatch(email="taken@example.com")
    second_mock_user = DBUserFactory.build(email=update_data.email)
    token = "valid.jwt.token"

    mock_auth_svc.get_user_from_token.return_value = mock_user
    mock_user_repo.get_by_username.return_value = None
    mock_user_repo.get_by_email.return_value = second_mock_user

    with pytest.raises(HTTPException) as exc_info:
        await user_svc.update_me(update_data, token)

    assert exc_info.value.status_code == status.HTTP_409_CONFLICT
    assert "Email already registered" in exc_info.value.detail
    mock_user_repo.update_by_id.assert_not_called()


@pytest.mark.unit
async def test_delete_me_success(user_service_with_mocks):
    user_svc, mock_auth_svc, mock_user_repo = user_service_with_mocks
    mock_user = DBUserFactory.build()
    token = "valid.jwt.token"

    mock_auth_svc.get_user_from_token.return_value = mock_user

    await user_svc.delete_me(token)

    mock_user_repo.delete_by_id.assert_called_once_with(user_id=mock_user.id)
