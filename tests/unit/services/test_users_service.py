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

from tests.factories import DBUserFactory


@pytest.fixture
def user_service_with_mocks():
    mock_user_repo = AsyncMock(spec=user_repository.UserRepository)
    mock_auth_svc = AsyncMock(spec=auth_service.AuthService)

    user_svc = user_service.UserService(mock_user_repo, mock_auth_svc)

    return user_svc, mock_auth_svc, mock_user_repo


@pytest.mark.unit
async def test_update_me_one_field_success(user_service_with_mocks):
    user_svc, mock_auth_svc, mock_user_repo = user_service_with_mocks
    user = DBUserFactory.build()
    update_data = user_schemas.UserPatch(username="newusername")

    mock_user_repo.get_by_username.return_value = None
    mock_user_repo.update_by_id.return_value = user

    result = await user_svc.update_me(update_data, user)

    assert result == user
    mock_user_repo.get_by_username.assert_called_once_with("newusername")
    mock_user_repo.update_by_id.assert_called_once()


@pytest.mark.unit
async def test_update_me_multiple_fields_success(user_service_with_mocks):
    user_svc, mock_auth_svc, mock_user_repo = user_service_with_mocks
    user = DBUserFactory.build()
    update_data = user_schemas.UserPatch(
        username="newusername",
        email="new@example.com",
    )

    mock_user_repo.get_by_username.return_value = None
    mock_user_repo.get_by_email.return_value = None
    mock_user_repo.update_by_id.return_value = user

    result = await user_svc.update_me(update_data, user)

    assert result == user
    mock_user_repo.get_by_username.assert_called_once_with(update_data.username)
    mock_user_repo.get_by_email.assert_called_once_with(update_data.email)
    mock_user_repo.update_by_id.assert_called_once()


@pytest.mark.unit
@patch.object(PasswordHasher, "hash", return_value="hashed-password")
async def test_update_me_password_hashed(mock_hash, user_service_with_mocks):
    user_svc, mock_auth_svc, mock_user_repo = user_service_with_mocks
    user = DBUserFactory.build()
    update_data = user_schemas.UserPatch(password="newpassword123")

    mock_user_repo.update_by_id.return_value = user

    await user_svc.update_me(update_data, user)

    mock_hash.assert_called_once_with(update_data.password)
    mock_user_repo.update_by_id.assert_called_once_with(
        user_id=user.id, update_data={"hashed_password": "hashed-password"}
    )


@pytest.mark.unit
async def test_update_me_conflict_username(user_service_with_mocks):
    user_svc, mock_auth_svc, mock_user_repo = user_service_with_mocks
    user = DBUserFactory.build()
    update_data = user_schemas.UserPatch(username="taken")
    second_mock_user = DBUserFactory.build(username=update_data.username)

    mock_user_repo.get_by_username.return_value = second_mock_user

    with pytest.raises(HTTPException) as exc_info:
        await user_svc.update_me(update_data, user)

    assert exc_info.value.status_code == status.HTTP_409_CONFLICT
    assert "Username already taken" in exc_info.value.detail
    mock_user_repo.update_by_id.assert_not_called()


@pytest.mark.unit
async def test_update_me_conflict_email(user_service_with_mocks):
    user_svc, mock_auth_svc, mock_user_repo = user_service_with_mocks
    user = DBUserFactory.build()
    update_data = user_schemas.UserPatch(email="taken@example.com")
    second_user = DBUserFactory.build(email=update_data.email)

    mock_user_repo.get_by_username.return_value = None
    mock_user_repo.get_by_email.return_value = second_user

    with pytest.raises(HTTPException) as exc_info:
        await user_svc.update_me(update_data, user)

    assert exc_info.value.status_code == status.HTTP_409_CONFLICT
    assert "Email already registered" in exc_info.value.detail
    mock_user_repo.update_by_id.assert_not_called()


@pytest.mark.unit
async def test_delete_me_success(user_service_with_mocks):
    user_svc, mock_auth_svc, mock_user_repo = user_service_with_mocks
    user = DBUserFactory.build()

    await user_svc.delete_me(user)

    mock_user_repo.delete_by_id.assert_called_once_with(user_id=user.id)
