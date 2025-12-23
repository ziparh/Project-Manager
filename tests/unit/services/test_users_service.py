import pytest
from fastapi import HTTPException, status
from unittest.mock import AsyncMock, patch

from modules.users import (
    repository as user_repository,
    service as user_service,
    schemas as user_schemas,
)
from core.security.password import PasswordHasher

from tests.factories.models import UserModelFactory


@pytest.fixture
def mock_user_repo():
    """Mock user repository"""
    return AsyncMock(spec=user_repository.UserRepository)


@pytest.fixture
def user_svc(mock_user_repo):
    """User service with mocked user repository"""
    return user_service.UserService(user_repo=mock_user_repo)


@pytest.mark.unit
class TestUpdateMe:
    async def test_one_field_success(self, user_svc, mock_user_repo):
        user = UserModelFactory.build()
        update_data = user_schemas.UserPatch(username="newusername")

        mock_user_repo.get_by_username.return_value = None
        mock_user_repo.update_by_id.return_value = user

        result = await user_svc.update_me(update_data, user)

        assert result == user
        mock_user_repo.get_by_username.assert_called_once_with("newusername")
        mock_user_repo.update_by_id.assert_called_once()

    async def test_multiple_fields_success(self, user_svc, mock_user_repo):
        user = UserModelFactory.build()
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

    @patch.object(PasswordHasher, "hash", return_value="hashed-password")
    async def test_password_hashed(self, mock_hash, user_svc, mock_user_repo):
        user = UserModelFactory.build()
        update_data = user_schemas.UserPatch(password="newpassword123")

        mock_user_repo.update_by_id.return_value = user

        await user_svc.update_me(update_data, user)

        mock_hash.assert_called_once_with(update_data.password)
        mock_user_repo.update_by_id.assert_called_once_with(
            user_id=user.id, update_data={"hashed_password": "hashed-password"}
        )

    async def test_conflict_username(self, user_svc, mock_user_repo):
        user = UserModelFactory.build()
        update_data = user_schemas.UserPatch(username="taken")
        second_mock_user = UserModelFactory.build(username=update_data.username)

        mock_user_repo.get_by_username.return_value = second_mock_user

        with pytest.raises(HTTPException) as exc_info:
            await user_svc.update_me(update_data, user)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "Username already taken" in exc_info.value.detail
        mock_user_repo.update_by_id.assert_not_called()

    async def test_conflict_email(self, user_svc, mock_user_repo):
        user = UserModelFactory.build()
        update_data = user_schemas.UserPatch(email="taken@example.com")
        second_user = UserModelFactory.build(email=update_data.email)

        mock_user_repo.get_by_username.return_value = None
        mock_user_repo.get_by_email.return_value = second_user

        with pytest.raises(HTTPException) as exc_info:
            await user_svc.update_me(update_data, user)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "Email already registered" in exc_info.value.detail
        mock_user_repo.update_by_id.assert_not_called()


@pytest.mark.unit
class TestDeleteMe:
    async def test_success(self, user_svc, mock_user_repo):
        user = UserModelFactory.build()

        await user_svc.delete_me(user)

        mock_user_repo.delete_by_id.assert_called_once_with(user_id=user.id)
